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
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    df = pd.DataFrame(rows)

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")
    df["cost"] = df["cost"].divide(1000000).round(2)
    df["cpc"] = df["cpc"].divide(1000000)
    df = df.convert_dtypes()

    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data", ttl="1d")
def get_fb_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
            SELECT 
            campaign_id,
            data_date_start as segment_date ,
            campaign_name,
            PARSE_NUMERIC(a.value) as mobile_app_install,  
            clicks,
            impressions,
            spend as cost,
            cpc,
            start_time as campaign_start_date, 
            end_time as campaign_end_date,
            reach,
            "Facebook" as source,
            0 as button_clicks,
            FROM dataexploration-193817.marketing_data.facebook_ads_data as d
            JOIN UNNEST(actions) as a
            WHERE a.action_type = 'mobile_app_install'
            and
            d.start_time >= '2021-01-01'
            order by data_date_start desc;

             """

    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["campaign_start_date"] = pd.to_datetime(
        df.campaign_start_date, utc=True
    ).dt.strftime("%Y/%m/%d")
    df["campaign_end_date"] = pd.to_datetime(
        df.campaign_end_date, utc=True
    ).dt.strftime("%Y/%m/%d")

    df["mobile_app_install"] = pd.to_numeric(df["mobile_app_install"])

    return df


@st.cache_data(ttl="1d", show_spinner=False)
# Looks for the string following the dash and makes that the associated country.
# This requires a strict naming convention of "[anything without dashes] - [country]]"
def add_campaign_country(df):

    regex_pattern = r"^[^-]*-[^-]*$"  # This regex pattern matches strings containing exactly one "-"

    df = df[df["campaign_name"].str.contains(regex_pattern)]

    # Set country to everything after the dash and remove padding
    regex_pattern = r"-\s*(.*)"
    df["country"] = df["campaign_name"].str.extract(regex_pattern)[0].str.strip()

    # Remove the word "Campaign" if it exists
    regex_pattern = r"\s*(.*)Campaign"
    extracted = df["country"].str.extract(regex_pattern)

    # Replace NaN values (no match) with the original values=
    df["country"] = extracted[0].fillna(df["country"])
    df["country"] = df["country"].str.strip()

    return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_google_campaign_conversions():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT campaign_id,
                metrics_conversions as button_clicks,
                FROM `dataexploration-193817.marketing_data.ads_CampaignConversionStats_6687569935`
                where segments_conversion_action_name like '%CTA_Gplay%';
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")

    return df


# This function takes a campaign based dataframe and sums it up into a single row per campaign.  The original dataframe
# has many entries per campaign based on daily extractions.
def rollup_campaign_data(df):

    # This will roll everything up except when there is multiple campaign names
    # for a campaign_id.  This happens when campaigns are renamed.
    df = df.groupby(["campaign_id", "campaign_name"], as_index=False).agg(
        {
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
    )

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
    combined = duplicates.groupby(["campaign_id"], as_index=False).agg(
        {
            "campaign_name": "last",
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
    )

    # put it all back together
    df = pd.concat([df, combined])

    return df


# Get the button clicks from BigQuery, add them to the dataframe
# and rollup the sum per campaign_id
def add_google_button_clicks(df):

    df_goog_conversions = campaigns.get_google_campaign_conversions()

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
