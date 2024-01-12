import streamlit as st
import pandas as pd
from rich import print as print

@st.cache_data(ttl="1d",show_spinner="Gathering User List")
def get_users_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                FROM `dataexploration-193817.user_data.users_data`
                ;
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    return df

@st.cache_data(ttl="1d",show_spinner=False)
def get_language_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT app_language
                FROM `dataexploration-193817.user_data.language_max_level`
                ;
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    return df