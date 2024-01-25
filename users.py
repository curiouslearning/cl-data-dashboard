import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np


@st.cache_data(ttl="1d", show_spinner="Gathering User List")
def get_users_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.users_data`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','2021/01/01') AND CURRENT_DATE() 
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_language_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT app_language
                FROM `dataexploration-193817.user_data.language_max_level`
                ;
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    lang_list = np.array(df.values).flatten().tolist()
    lang_list = [x.strip(" ") for x in lang_list]
    return lang_list


@st.cache_data(ttl="1d", show_spinner=False)
def get_country_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                FROM `dataexploration-193817.user_data.active_countries`
                order by country asc
                ;
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    countries_list = np.array(df.values).flatten().tolist()
    return countries_list
