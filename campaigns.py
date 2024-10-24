import streamlit as st
import pandas as pd
from rich import print as print
import campaigns
import metrics
import asyncio
from pyinstrument import Profiler


# Starting 05/01/2024, campaign names were changed to support an indication of 
# both language and country through a naming convention.  So we are only collecting
# and reporting on daily campaign segment data from that day forward.

# Combined function to fetch Google and Facebook campaign data concurrently

async def get_campaign_data():
    p = Profiler(async_mode="disabled")
    with p:
        bq_client = st.session_state.bq_client

        # Helper function to run BigQuery queries asynchronously
        async def run_query(query):
            return await asyncio.to_thread(bq_client.query(query).to_dataframe)

        # Google Ads Query
        google_ads_query = """
            SELECT
                metrics.campaign_id,
                metrics.segments_date as segment_date,
                campaigns.campaign_name,
                metrics_cost_micros as cost,
                campaigns.campaign_start_date,
                campaigns.campaign_end_date, 
                "Google" as source
            FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
            INNER JOIN dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
            ON metrics.campaign_id = campaigns.campaign_id
            AND metrics.segments_date >= '2024-05-01'
            GROUP BY 1,2,3,4,5,6
        """

        # Facebook Ads Query
        facebook_ads_query = """
            SELECT 
                d.campaign_id,
                d.data_date_start as segment_date,
                d.campaign_name,
                d.spend as cost,
                d.start_time as campaign_start_date, 
                d.end_time as campaign_end_date,
                "Facebook" as source
            FROM dataexploration-193817.marketing_data.facebook_ads_data as d
            WHERE d.data_date_start >= '2024-05-01'
            ORDER BY d.data_date_start DESC;
        """

        # Run both queries concurrently using asyncio.gather
        google_ads_data, facebook_ads_data = await asyncio.gather(
            run_query(google_ads_query),
            run_query(facebook_ads_query)
        )

        # Process Google Ads Data
        google_ads_data["campaign_id"] = google_ads_data["campaign_id"].astype(str).str.replace(",", "")
        google_ads_data["cost"] = google_ads_data["cost"].divide(1000000).round(2)
  #      google_ads_data["segment_date"] = pd.to_datetime
        google_ads_data["segment_date"] = pd.to_datetime(google_ads_data["segment_date"])
    p.print(color="red")
    return google_ads_data, facebook_ads_data

@st.cache_data(ttl="1d", show_spinner=False)
# Looks for the string following the dash and makes that the associated country.
# This requires a strict naming convention of "[anything without dashes] - [country]]"
def add_country_and_language(df):

    # Define the regex patterns
    country_regex_pattern = r"-\s*(.*)"
    language_regex_pattern = r":\s*([^-]+?)\s*-"
    campaign_regex_pattern = r"\s*(.*)Campaign"

    # Extract the country
    df["country"] = (
        df["campaign_name"].str.extract(country_regex_pattern)[0].str.strip()
    )

    # Remove the word "Campaign" if it exists in the country field
    extracted = df["country"].str.extract(campaign_regex_pattern)
    df["country"] = extracted[0].fillna(df["country"]).str.strip()

    # Extract the language
    df["app_language"] = (
        df["campaign_name"].str.extract(language_regex_pattern)[0].str.strip()
    )

    # Set default values to None where there's no match
    country_contains_pattern = r"-\s*(?:.*)"
    language_contains_pattern = r":\s*(?:[^-]+?)\s*-"

    df["country"] = df["country"].where(
        df["campaign_name"].str.contains(
            country_contains_pattern, regex=True, na=False
        ),
        None,
    )
    df["app_language"] = df["app_language"].where(
        df["campaign_name"].str.contains(
            language_contains_pattern, regex=True, na=False
        ),
        None,
    ).str.lower()

    return df


# This function takes a campaign based dataframe and sums it up into a single row per campaign.  The original dataframe
# has many entries per campaign based on daily extractions.
def rollup_campaign_data(df):
    aggregation = {
        "segment_date": "last",
        "campaign_start_date": "first",
        "campaign_end_date": "first",
        "source": "first",
        "cost": "sum",
    }
    optional_columns = ["country", "app_language"]
    for col in optional_columns:
        if col in df.columns:
            aggregation[col] = "first"

    # find duplicate campaign_ids, create a dataframe for them and remove from original
    duplicates = df[df.duplicated("campaign_id", keep=False)]
    df = df.drop_duplicates("campaign_id", keep=False)

    # Get the newest campaign info according to segment date and use its campaign_name
    # for the other campaign names.
    duplicates = duplicates.sort_values(by="segment_date", ascending=False)
    duplicates["campaign_name"] = duplicates.groupby("campaign_id")[
        "campaign_name"
    ].transform("first")

    # Do another rollup on the duplicates.  This time the campaign name will be the same
    # so we can take any of them
    aggregation["campaign_name"] = "first"
    combined = duplicates.groupby(["campaign_id"], as_index=False).agg(aggregation)

    # put it all back together
    df = pd.concat([df, combined])
    df = df.drop(columns=["segment_date"])

    return df



@st.cache_data(ttl="1d", show_spinner=False)
def get_campaigns_by_date(daterange):
    df_campaigns_all = st.session_state.df_campaigns_all

    conditions = [
        f"@daterange[0] <= segment_date <= @daterange[1]",
    ]

    query = " and ".join(conditions)
    df = df_campaigns_all.query(query)

    df = campaigns.rollup_campaign_data(df)
    df = campaigns.add_google_button_clicks(df, daterange)

    return df


@st.cache_data(ttl="1d", show_spinner=True)
def build_campaign_table(df, daterange):

    df = (
        df.groupby(["country", "app_language"], as_index=False)
        .agg(
            {
                "cost": "sum",
            }
        )
        .round(2)
    )

    stats = ["LR", "PC", "LA","RA"]
    for idx, row in df.iterrows():
        country_list = [row["country"]]
        language = [row["app_language"].lower()]

        for stat in stats:

            result = metrics.get_totals_by_metric(
                countries_list=country_list,
                language=language,
                daterange=daterange,
                stat=stat,
                app="CR",
            )
            df.at[idx, stat] = result
            df.at[idx, stat + "C"] = (
                (df.at[idx, "cost"] / result).round(2) if result != 0 else 0
            )
            if stat == "LR":
                LR = result
            elif stat == "PC":
                PC = result
            elif stat == "LA":
                LA = result
            else:
                RA = result
        try:
            LA_LR = round(LA / LR, 2) * 100
            PC_LR = round(PC / LR, 2) * 100
            RA_LR = round(RA / LR, 2) * 100
        except ZeroDivisionError:
            LA_LR = 0
            PC_LR = 0
            RA_LR = 0
        df.at[idx, "PC_LR %"] = PC_LR
        df.at[idx, "LA_LR %"] = LA_LR
        df.at[idx, "RA_LR %"] = RA_LR

    return df
