import streamlit as st
import pandas as pd
from rich import print as print


@st.cache_data(show_spinner="Fetching Google Campaign Data")
def get_google_campaign_data(_bq_client):

    test = 20732448932
    sql_query = f"""
         SELECT metrics.campaign_id,
        metrics.segments_date as day,
        campaigns.campaign_name,
        campaigns.campaign_start_date,
        campaigns.campaign_end_date, 
        metrics_clicks as clicks,
        metrics_conversions as conversions,
        metrics_impressions as impressions,
        metrics_cost_micros as cost,
        metrics_average_cpc as cpc
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns
        on metrics.campaign_id = campaigns.campaign_id
 #       and campaigns.campaign_id = {test}
        group by 1,2,3,4,5,6,7,8,9,10
        order by segments_date desc        
    """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    
    df = pd.DataFrame(rows)
    
    df["campaign_id"]=df["campaign_id"].astype(str).str.replace(",", "")
    df["day"] = pd.to_datetime(df["day"]).dt.date
   # df["cost"] = float(df["cost"]) / 1000000
    df["Source"] = ("Google")
    df["mobile_app_install"] = 0  #Holding place until that metric is available
    
    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data")
def get_fb_campaign_data(_bq_client):

    sql_query = f"""
            SELECT 
            campaign_id,
            campaign_name,
            start_time as campaign_start_date, 
            end_time as campaign_end_date,
            data_date_start as day ,
            clicks,
            impressions,
            spend as cost,
            cpc,
            PARSE_NUMERIC(a.value) as mobile_app_install,  
            FROM dataexploration-193817.marketing_data.facebook_ads_data
            JOIN UNNEST(actions) as a
            WHERE a.action_type = 'mobile_app_install'
            """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    if (len(rows) == 0):
        return pd.DataFrame()

    df1 = pd.DataFrame(rows)
    df1["campaign_start_date"] = pd.to_datetime(df1.campaign_start_date,utc=True)
    df1["day"] = pd.to_datetime(df1["day"]).dt.date
    df1["campaign_start_date"] = df1['campaign_start_date'].dt.strftime('%Y/%m/%d')
    df1["Source"] = ("Facebook")

    return df1

