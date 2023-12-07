import streamlit as st
from rich import print
import pandas as pd
import numpy as np


@st.cache_data()
def get_ave_cost_per_action(daterange):

    df_all = st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1]')

    df.query('mobile_app_install > 0',inplace=True) # Only calculate for campaigns with installs

    total_downloads = df["mobile_app_install"].sum()
    total_cost = df["cost"].sum()   
    
    if (total_downloads > 0):
        return  float(total_cost) / float(total_downloads)
    
    return 0


@st.cache_data()
def get_download_totals(daterange):

    df_all= st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1]')
    total = df["mobile_app_install"].sum()
    
    return total

@st.cache_data()
def get_campaign_data_totals(daterange,source):

    df_all = st.session_state.df_all

    df = df_all.query('@daterange[0] <= day <= @daterange[1]  and Source == @source')

    pivot_df = pd.pivot_table(
        df,
        index=['campaign_id','campaign_name','campaign_start_date','campaign_end_date'],
        aggfunc={'mobile_app_install': np.sum,'clicks': np.sum, 'impressions': np.sum, 'cost': np.sum,'cpc': np.sum})  
    pivot_df = pivot_df.reset_index()
    pivot_df = pivot_df.set_index('campaign_name')

    pivot_df.sort_values(by=['campaign_name'],ascending=True)
    return pivot_df