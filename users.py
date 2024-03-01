import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np


# Firebase returns two different formats of user_pseudo_id between
# web app events and android events, so we have to run multiple queries
# instead of a join because we don't have a unique key for both
# This would all be unncessery if dev had included the app user id per the spec.
@st.cache_data(ttl="1d", show_spinner="Gathering User List")
def get_users_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.la_users_data`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','2021/01/01') AND CURRENT_DATE() 
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df_la = pd.DataFrame(rows)

    sql_query = f"""
            SELECT *
                FROM `dataexploration-193817.user_data.user_first_open_list`
            WHERE
                first_open BETWEEN PARSE_DATE('%Y/%m/%d','2021/01/01') AND CURRENT_DATE() 
            """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df_lr = pd.DataFrame(rows)

    sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.puzzle_completed_users`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','2021/01/01') AND CURRENT_DATE() 
                """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    df_lr = pd.DataFrame(rows)

    return df_la, df_lr


@st.cache_data(ttl="1d", show_spinner=False)
def get_language_list():
    lang_list = ["All"]
    if "bq_client" in st.session_state:
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
    countries_list = []
    if "bq_client" in st.session_state:
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


def debug_list():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        select distinct user_pseudo_id from `dataexploration-193817.user_data.user_first_open_list`      """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    df1 = pd.DataFrame(rows)

    sql_query = f"""
        select distinct user_pseudo_id from `dataexploration-193817.user_data.user_first_open_list`      """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    df2 = pd.DataFrame(rows)

    """

    duplicates = (
        df[df.duplicated(subset=["user_pseudo_id"], keep=False)]
    ).reset_index()
    df_no_duplicates = df.drop_duplicates(
        subset=["user_pseudo_id"], keep=False
    ).reset_index()
"""
    df3 = pd.merge(df1, df2, on="user_pseudo_id", how="inner")
    print("DEBUG")
    df3.info()

    return
