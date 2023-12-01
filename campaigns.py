import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np


@st.cache_data(show_spinner="Fetching Google Campaign Data")
def get_google_campaign_data_totals(_bq_client,daterange):

    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")
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
        and segments_date >= '{date_start}' and segments_date <= '{date_end}' 
 #       and campaigns.campaign_id = {test}
        group by 1,2,3,4,5,6,7,8,9,10
        order by segments_date desc        
    """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    
    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    df["Source"] = ("Google")
    df["campaign_id"]=df["campaign_id"].astype(str).str.replace(",", "")
    
    df = pd.pivot_table(
    df,
    index=['campaign_id','campaign_name','campaign_start_date','campaign_end_date'],
    aggfunc={'clicks': np.sum, 'conversions': np.sum, 'impressions': np.sum, 'cost': np.sum,'cpc': np.average})

    df = df.reset_index()
    df = df.set_index('campaign_name')
    return df


@st.cache_data(show_spinner="Fetching Facebook Campaign Data")
def get_fb_campaign_data_totals(_bq_client,daterange):
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")

    # This is a two query hack because I could not figure out how to work with the
    # RECORD column and get the data the way I want
    sql_query = f"""
        SELECT 
            campaign_id,
            campaign_name,
            start_time as campaign_start_date, 
            end_time as campaign_end_date,
            data_date_start as day,
            clicks,
            impressions,
            spend as cost,
            cpc 
            FROM dataexploration-193817.marketing_data.facebook_ads_data
            WHERE  data_date_start >= '{date_start}' AND data_date_start <= '{date_end}'
            """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    if (len(rows) == 0):
        return pd.DataFrame()

    df1 = pd.DataFrame(rows)
    df1["campaign_start_date"] = pd.to_datetime(df1.campaign_start_date,utc=True)
    df1["campaign_start_date"] = df1['campaign_start_date'].dt.strftime('%Y/%m/%d')
    
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
    merged_df = pd.pivot_table(
        merged_df,
        index=['campaign_id','campaign_name','campaign_start_date','campaign_end_date'],
        aggfunc={'clicks': np.sum, 'impressions': np.sum, 'cost': np.sum,'cpc': np.sum,'mobile_app_install': np.sum})
    
    merged_df["Source"] = ("Facebook")
    merged_df = merged_df.reset_index()
    merged_df = merged_df.set_index('campaign_name')
    return merged_df

