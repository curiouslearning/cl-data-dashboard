import streamlit as st
from rich import print
import pandas as pd
import datetime as dt



@st.cache_data(ttl="1d",show_spinner=False)
def get_ave_cost_per_action(daterange):

    df_all = st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1] and mobile_app_install > 0')

    total_downloads = df["mobile_app_install"].sum()
    total_cost = df["cost"].sum()   
    
    if (total_downloads > 0):
        return  float(total_cost) / float(total_downloads)
    
    return 0

@st.cache_data(ttl="1d",show_spinner=False)
def get_google_conversions(daterange):
    df = st.session_state.df_goog_conversions

    df1 = df.query('@daterange[0] <= day <= @daterange[1]')
    total = df1["button_clicks"].sum()
    return total


@st.cache_data(ttl="1d",show_spinner=False)
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
 
@st.cache_data(ttl="1d",show_spinner=False)
def get_LA_totals(daterange):
    bq_client = st.session_state.bq_client
    start_date = daterange[0].strftime('%Y/%m/%d')
    end_date = daterange[1].strftime('%Y/%m/%d')

    sql_query = f"""
            SELECT 
            count(*)
            FROM `dataexploration-193817.user_data.learner_aquired`
            WHERE
            event_date BETWEEN '{start_date}' AND '{end_date}'  ;

             """

    iterator = bq_client.query(sql_query).result()
    first_row = next(iterator)
    return first_row[0]


@st.cache_data(ttl="1d",show_spinner=False)
def get_LR_totals(daterange):
    bq_client = st.session_state.bq_client
    start_date = daterange[0].strftime('%Y/%m/%d')
    end_date = daterange[1].strftime('%Y/%m/%d')

    sql_query = f"""
            SELECT 
            count(*)
            FROM `dataexploration-193817.user_data.user_first_open_list`
            WHERE
            first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND PARSE_DATE('%Y/%m/%d','{end_date}')  ;

             """

    iterator = bq_client.query(sql_query).result()
    first_row = next(iterator)
    return first_row[0]

@st.cache_data(ttl="1d",show_spinner="Calculating GC")
def get_GC_avg(daterange):
    bq_client = st.session_state.bq_client
    start_date = daterange[0].strftime('%Y/%m/%d')
    end_date = daterange[1].strftime('%Y/%m/%d')

    sql_query = f"""
        SELECT
            user_pseudo_id,
            event_date,
            MAX(a.level) AS max_user_level,
            ROUND(SAFE_DIVIDE(MAX(a.level), b.max_level) * 100 )AS gc,
            b.max_level AS max_game_level
        FROM
         `dataexploration-193817.user_data.all_users` a
        LEFT JOIN (
        SELECT
            app_language,
            max_level
        FROM
            `dataexploration-193817.user_data.language_max_level`
        GROUP BY
            app_language,
            max_level ) b
        ON
            b.app_language = a.app_language
        AND
            event_date BETWEEN '{start_date}') AND '{end_date}' 
        GROUP BY
            a.user_pseudo_id,
            a.event_date,
            b.max_level      
        """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    
    df = pd.DataFrame(rows)
    m = df.mean('gc',numeric_only=True)
    return m
    
    


    