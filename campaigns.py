import streamlit as st
import pandas as pd

@st.cache_data
def get_google_campaign_data_totals(_bq_client,daterange):
    date_start = daterange[0].strftime("%Y-%m-%d")
    sql_query = f"""
        SELECT metrics.campaign_id,
        campaigns.campaign_name,
        campaigns.campaign_start_date,
        campaigns.campaign_end_date, 
        sum(metrics_clicks) as clicks,
        sum(metrics_conversions) as conversions,
        sum(metrics_impressions) as impressions,
        sum(metrics_cost_micros) as cost,
        avg(metrics_average_cpc) as cpc, 
        sum(metrics_conversions) as conversions,
        sum(metrics_conversions_value)
       
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns on metrics.campaign_id = campaigns.campaign_id
        WHERE  campaigns.campaign_start_date >= '{date_start}'
        group by metrics.campaign_id,campaigns.campaign_name,campaigns.campaign_start_date,campaigns.campaign_end_date
    """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df = pd.DataFrame(rows)
    df["Source"] = ("Google")
    return df

@st.cache_data
def get_fb_campaign_data_totals(_bq_client,daterange):
    date_start = daterange[0].strftime("%Y-%m-%d")

    sql_query = f"""
        SELECT campaign_id,
        campaign_name,
        start_time,
        end_time, 
        sum(clicks) as clicks,
        sum(impressions) as impressions,
        sum(spend) as cost,
        avg(cpc) as cpc, 
        a.action_type,
        sum(PARSE_NUMERIC(a.value)) as mobile_app_downloads,       
        FROM dataexploration-193817.marketing_data.facebook_ads_data
        JOIN UNNEST(actions) as a  
        WHERE  start_time >= '{date_start}'
        group by campaign_id,campaign_name,start_time,end_time,a.action_type;   """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df = pd.DataFrame(rows)
    df["Source"] = ("Facebook")
    return df
