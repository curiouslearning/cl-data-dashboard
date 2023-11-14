import streamlit as st
import pandas as pd

@st.cache_data
def get_campaign_data(_bq_client):
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
       
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_8779787641 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_8779787641 as campaigns on metrics.campaign_id = campaigns.campaign_id
        group by metrics.campaign_id,campaigns.campaign_name,campaigns.campaign_start_date,campaigns.campaign_end_date
    """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df_google = pd.DataFrame(rows)
    df_google["Source"] = ("Google")
    return df_google
