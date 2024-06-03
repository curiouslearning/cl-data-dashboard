import streamlit as st
import pandas as pd
from rich import print as print
import campaigns
from collections import defaultdict


@st.cache_data(show_spinner="Fetching Google Campaign Data", ttl="1d")
def get_google_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        SELECT
        metrics.campaign_id,
        metrics.segments_date as segment_date,
        campaigns.campaign_name,
        0 as mobile_app_install,
        metrics_clicks as clicks,
        metrics_impressions as impressions,
        metrics_cost_micros as cost,
        metrics_average_cpc as cpc,
        campaigns.campaign_start_date,
        campaigns.campaign_end_date, 
        0 as reach,
        "Google" as source
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
        on metrics.campaign_id = campaigns.campaign_id
        and campaigns.campaign_start_date >= '2021-01-01'
        group by 1,2,3,4,5,6,7,8,9,10   
    """

    df = bq_client.query(sql_query).to_dataframe()

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")
    df["cost"] = df["cost"].divide(1000000).round(2)
    df["cpc"] = df["cpc"].divide(1000000)
    df["segment_date"] = pd.to_datetime(df["segment_date"])
    df["segment_date"] = df["segment_date"].values.astype("datetime64[D]")

    df = df.convert_dtypes()

    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data", ttl="1d")
def get_fb_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        SELECT 
            d.campaign_id,
            d.data_date_start as segment_date,
            d.campaign_name,
            COALESCE(
                (SELECT PARSE_NUMERIC(a.value)
                 FROM UNNEST(d.actions) as a
                 WHERE a.action_type = 'mobile_app_install'
                 LIMIT 1), 0) as mobile_app_install,
            d.clicks,
            d.impressions,
            d.spend as cost,
            d.cpc,
            d.start_time as campaign_start_date, 
            d.end_time as campaign_end_date,
            d.reach,
            "Facebook" as source
        FROM dataexploration-193817.marketing_data.facebook_ads_data as d
        WHERE d.start_time >= '2021-01-01'
        #        and d.campaign_id in ('120206573803000195')
        ORDER BY d.data_date_start DESC;
        """
    df = bq_client.query(sql_query).to_dataframe()

    # in case the importer runs more than once on the same day, delete any duplicates
    df = df.drop_duplicates(subset=["campaign_id", "segment_date"], keep="first")

    df["campaign_start_date"] = pd.to_datetime(
        df.campaign_start_date, utc=True
    ).dt.strftime("%Y/%m/%d")
    df["campaign_end_date"] = pd.to_datetime(
        df.campaign_end_date, utc=True
    ).dt.strftime("%Y/%m/%d")

    df["segment_date"] = pd.to_datetime(df["segment_date"])
    df["segment_date"] = df["segment_date"].values.astype("datetime64[D]")

    df["mobile_app_install"] = pd.to_numeric(df["mobile_app_install"])

    return df


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
    )
    return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_google_campaign_conversions(daterange):
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT campaign_id,
                metrics_conversions as button_clicks,
                FROM `dataexploration-193817.marketing_data.ads_CampaignConversionStats_6687569935`
                where segments_conversion_action_name like '%CTA_Gplay%'
               AND DATE(segments_date) BETWEEN '{daterange[0].strftime("%Y-%m-%d")}' AND '{daterange[1].strftime("%Y-%m-%d")}' ;
                
                """

    df = bq_client.query(sql_query).to_dataframe()

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")

    return df


# This function takes a campaign based dataframe and sums it up into a single row per campaign.  The original dataframe
# has many entries per campaign based on daily extractions.
def rollup_campaign_data(df):
    aggregation = {
        "segment_date": "last",
        "campaign_start_date": "first",
        "campaign_end_date": "first",
        "mobile_app_install": "sum",
        "source": "first",
        "clicks": "sum",
        "reach": "sum",
        "cost": "sum",
        "cpc": "sum",
        "impressions": "sum",
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


# Get the button clicks from BigQuery, add them to the dataframe
# and rollup the sum per campaign_id
def add_google_button_clicks(df, daterange):

    df_goog_conversions = campaigns.get_google_campaign_conversions(daterange)

    df_goog = pd.merge(
        df,
        df_goog_conversions,
        on="campaign_id",
        how="left",
        suffixes=("", ""),
    )

    df_goog = df_goog.groupby("campaign_id", as_index=False).agg(
        {
            "campaign_name": "last",
            "app_language": "first",
            "country": "first",
            "campaign_start_date": "first",
            "campaign_end_date": "first",
            "mobile_app_install": "first",
            "source": "first",
            "button_clicks": "sum",
            "clicks": "first",
            "reach": "first",
            "cost": "first",
            "cpc": "first",
            "impressions": "first",
        }
    )

    return df_goog
