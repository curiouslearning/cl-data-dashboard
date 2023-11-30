import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np


@st.cache_data
def get_google_campaign_data_totals(_bq_client,daterange):
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")

    sql_query = f"""
        SELECT metrics.campaign_id,
        campaigns.campaign_name,
        sum(metrics_clicks) as clicks,
        sum(metrics_conversions) as conversions,
        sum(metrics_impressions) as impressions,
        sum(metrics_cost_micros) as cost,
        avg(metrics_average_cpc) as cpc, 
        sum(metrics_conversions) as conversions
        
       
        FROM dataexploration-193817.marketing_data.p_ads_CampaignStats_6687569935 as metrics
        inner join dataexploration-193817.marketing_data.ads_Campaign_6687569935 as campaigns on metrics.campaign_id = campaigns.campaign_id
        WHERE  campaigns.campaign_start_date >= '{date_start}' AND campaigns.campaign_start_date <= '{date_end}'
        group by metrics.campaign_id,campaigns.campaign_name
    """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    
    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    df["Source"] = ("Google")
    df["campaign_id"]=df["campaign_id"].astype(str).str.replace(",", "")

    return df


@st.cache_data
def get_fb_campaign_data_totals(_bq_client,daterange):
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")

    # This is a two query hack because I could not figure out how to work with the
    # RECORD column and get the data the way I want
    sql_query = f"""
        SELECT 
            campaign_id,
            campaign_name,
            sum(clicks) as clicks,
            sum(impressions) as impressions,
            sum(spend) as cost,
            avg(cpc) as cpc, 
            FROM dataexploration-193817.marketing_data.facebook_ads_data
            WHERE  data_date_start >= '{date_start}' AND data_date_start <= '{date_end}'
            group by campaign_id,campaign_name;
            """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    if (len(rows) == 0):
        return pd.DataFrame()

    df1 = pd.DataFrame(rows)
   # df1["campaign_start_date"] = pd.to_datetime(df1.campaign_start_date,utc=True)
   # df1["campaign_start_date"] = df1['campaign_start_date'].dt.strftime('%Y/%m/%d')
    
    sql_query = f"""
       SELECT 
        campaign_id,
        sum(PARSE_NUMERIC(a.value)) as mobile_app_install,       
        FROM dataexploration-193817.marketing_data.facebook_ads_data
        JOIN UNNEST(actions) as a  
        WHERE a.action_type = 'mobile_app_install'
        AND start_time >= '{date_start}' AND start_time <= '{date_end}'
        group by campaign_id;    """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df2 = pd.DataFrame(rows)
    
    merged_df = pd.merge(df1, df2, on='campaign_id', how='left')
    merged_df['mobile_app_install'].fillna(0, inplace=True)
    pd.pivot_table(
        merged_df,
        index=['campaign_id'],
        aggfunc={'clicks': np.sum, 'impressions': np.sum, 'cost': np.sum,'cpc': np.sum,'mobile_app_install': np.sum})
    
    merged_df["Source"] = ("Facebook")
    return merged_df

