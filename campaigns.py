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
    df["mobile_app_install"] = 0  # Holding place until that metric is available
    df.reset_index(drop=True, inplace=True)
    df.set_index("campaign_id")

    df = add_campaign_country(df)
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
            data_date_start as day 
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
        df.campaign_start_date, utc=True
    ).dt.strftime("%Y/%m/%d")
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["source"] = "Facebook"
    df["mobile_app_install"] = pd.to_numeric(df["mobile_app_install"])
    df.reset_index(drop=True, inplace=True)
    df.set_index("campaign_id")

    df = add_campaign_country(df)

    return df


@st.cache_data(ttl="1d", show_spinner=False)
def add_campaign_country(df):
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                FROM `dataexploration-193817.user_data.campaign_gsheet`;
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    dfcountry = pd.DataFrame(rows)
    if len(rows) == 0:
        return pd.DataFrame()

    merged_df = pd.merge(df, dfcountry, on="campaign_id", how="left")

    # Step 2: Drop rows from DataFrame A where there's no match in DataFrame B
    df = df[df["campaign_id"].isin(dfcountry["campaign_id"].dropna())]

    # Step 3: Update DataFrame A with the values from the merged column
    df["country"] = merged_df["country"]

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
