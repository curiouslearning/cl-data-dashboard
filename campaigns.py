import streamlit as st
import pandas as pd
from rich import print as print


@st.cache_data(show_spinner="Fetching Google Campaign Data", ttl="1d")
def get_google_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        SELECT
        metrics.campaign_id,
        metrics.segments_date as day,
        campaigns.campaign_name,
        metrics_clicks as clicks,
        metrics_conversions as all_conversions,
        metrics_impressions as impressions,
        metrics_cost_micros as cost,
        metrics_average_cpc as cpc,
        campaigns.campaign_start_date,
        campaigns.campaign_end_date, 
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
        on metrics.campaign_id = campaigns.campaign_id
        and campaigns.campaign_start_date >= '2021-01-01'
        group by 1,2,3,4,5,6,7,8,9,10
        order by segments_date desc        
    """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    df = pd.DataFrame(rows)

    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["cost"] = df["cost"].divide(1000000).round(2)
    df["cpc"] = df["cpc"].divide(1000000)
    df = df.convert_dtypes()

    df["source"] = "Google"
    df["mobile_app_install"] = 0  # Facebook only metric
    df["reach"] = 0  # Facebook only metric

    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data", ttl="1d")
def get_fb_campaign_data():
    bq_client = st.session_state.bq_client
    sql_query = f"""
            SELECT 
            campaign_id,
            campaign_name,
            PARSE_NUMERIC(a.value) as mobile_app_install,  
            clicks,
            impressions,
            spend as cost,
            cpc,
            start_time as campaign_start_date, 
            end_time as campaign_end_date,
            data_date_start as day,
            0 as button_clicks,
            reach
            FROM dataexploration-193817.marketing_data.facebook_ads_data as d
            JOIN UNNEST(actions) as a
            WHERE a.action_type = 'mobile_app_install'
            and
            d.start_time >= '2021-01-01';

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
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["source"] = "Facebook"
    df["mobile_app_install"] = pd.to_numeric(df["mobile_app_install"])

    return df


@st.cache_data(ttl="1d", show_spinner=False)
def add_campaign_country(df):
    pattern = "-" + "(.*)"

    # Extract characters following the string match and assign it as the "country"
    df["country"] = df["campaign_name"].str.extract(pattern)

    # Remove the word "Campaign" if it exists
    pattern = "(.*)Campaign"
    extracted = df["country"].str.extract(pattern)
    # Strip leading spaces from the extracted string
    extracted[0] = extracted[0].str.strip()
    # Replace NaN values (no match) with the original values=
    df["country"] = extracted[0].fillna(df["country"])

    df["country"] = extracted[0].str.strip()
    return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_google_campaign_conversions():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT campaign_id,
                metrics_conversions as button_clicks,
                segments_date as day
                FROM `dataexploration-193817.marketing_data.ads_CampaignConversionStats_6687569935`
                where segments_conversion_action_name like '%CTA_Gplay%';
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["source"] = "Google"
    df["campaign_id"] = df["campaign_id"].astype(str).str.replace(",", "")
    df.reset_index(drop=True, inplace=True)
    df.set_index("campaign_id")

    return df


def rollup_campaign_data(df):
    return df.groupby("campaign_id", as_index=True).agg(
        {
            "campaign_name": "first",
            "campaign_start_date": "first",
            "campaign_end_date": "first",
            "mobile_app_install": "sum",
            "day": "first",
            "source": "first",
            "clicks": "sum",
            "reach": "first",
            "button_clicks": lambda x: (
                x.sum() if "button_clicks" in x else 0
            ),  # Sum if column exists, otherwise return 0
            "cost": "sum",
            "cpc": "sum",
            "impressions": "sum",
        }
    )
