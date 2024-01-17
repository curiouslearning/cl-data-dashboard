import streamlit as st
from rich import print
import pandas as pd
import datetime as dt
import numpy as np



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
 
@st.cache_data(ttl="1d",show_spinner="Getting LA")
def get_LA_totals(daterange,countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query('@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list) and max_user_level >= 1')
    return len(df_user_list)


@st.cache_data(ttl="1d",show_spinner=False)
def get_LR_totals(daterange,countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query('@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list)')
    return len(df_user_list)

@st.cache_data(ttl="1d",show_spinner="Calculating GC")
def get_GC_avg_by_date(daterange,countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query('@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list)')
    return  np.average(df_user_list.gc)
    


    