import streamlit as st
from rich import print
import pandas as pd
import datetime as dt



@st.cache_data(ttl="1d")
def get_ave_cost_per_action(daterange):

    df_all = st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1] and mobile_app_install > 0')

    total_downloads = df["mobile_app_install"].sum()
    total_cost = df["cost"].sum()   
    
    if (total_downloads > 0):
        return  float(total_cost) / float(total_downloads)
    
    return 0


@st.cache_data(ttl="1d")
def get_first_open_totals(daterange):

    df_events= st.session_state.df_events

    df = df_events.query('@daterange[0] <= day <= @daterange[1]')
    total = len(df)
    
    return total

@st.cache_data(ttl="1d")
def get_download_totals(daterange):

    df_all = st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1]')
    total = df["mobile_app_install"].sum()
    
    return total

@st.cache_data(ttl="1d")
def get_google_conversions(daterange):
    df = st.session_state.df_goog_conversions

    df1 = df.query('@daterange[0] <= day <= @daterange[1]')
    total = df1["button_clicks"].sum()
    return total


@st.cache_data(ttl="1d")
def get_campaign_data_totals(daterange,source):

    df_all = st.session_state.df_all
 
    df = df_all.query('@daterange[0] <= day <= @daterange[1]  and source == @source')
    df = (df.groupby('campaign_id', as_index=True)
            .agg({'campaign_name': 'first',
                'campaign_start_date': 'first',
                'campaign_end_date': 'first',
                'mobile_app_install': 'sum',
                'clicks': 'sum',
                'button_clicks': 'sum',
                'cost': 'sum',
                'cpc': 'sum',
                'impressions': 'sum'})
            )
    
    df.sort_values(by=['campaign_start_date'],ascending=False)

    return df

@st.cache_data(ttl="1d")
def get_first_open_totals(daterange):
    bq_client = st.session_state.bq_client
    start_date = daterange[0].strftime('%Y/%m/%d')
    end_date = daterange[1].strftime('%Y/%m/%d')



    sql_query = f"""
            SELECT 
            count(*)
            FROM dataexploration-193817.play_data.events
            WHERE
#           parse_date('%Y%m%d',event_date) BETWEEN '{start_date}' AND '{end_date}'  ;
            parse_date('%Y%m%d',event_date) BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND PARSE_DATE('%Y/%m/%d','{end_date}')  ;

             """

    iterator = bq_client.query(sql_query).result()
    first_row = next(iterator)
    return first_row[0]



