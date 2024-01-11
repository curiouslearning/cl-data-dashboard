import streamlit as st
import pandas as pd
from rich import print as print

@st.cache_data(ttl="1d",show_spinner="Gathering User List")
def get_users_list(_bq_client):
    sql_query = f"""
                SELECT *
                FROM `dataexploration-193817.user_data.users_data`
                ;
                """
    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    return df