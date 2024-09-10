import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np
from pyinstrument import Profiler
import logging


# How far back to obtain user data.  Currently the queries pull back to 01/01/2021
start_date = "2021/01/01"


# Firebase returns two different formats of user_pseudo_id between
# web app events and android events, so we have to run multiple queries
# instead of a join because we don't have a unique key for both
# This would all be unncessery if dev had included the app user id per the spec.
@st.cache_data(ttl="1d", show_spinner="Gathering User List")
def get_users_list():
    p = Profiler(async_mode="disabled")
    with p:

        bq_client = st.session_state.bq_client
        
        # All Unity users and their progress are stored in one table
        sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.unity_user_progress`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
                """

        df_unity_users = bq_client.query(sql_query).to_dataframe()

        # These are distinct first_open events for CR - will not contain app_language so can only be used for FO counts
        sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.cr_first_open`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
                """

        df_cr_first_open = bq_client.query(sql_query).to_dataframe()

        # All users in the funnel from DC down
        sql_query = f"""
                    SELECT *
                        FROM `dataexploration-193817.user_data.cr_user_progress`
                    WHERE
                        first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
                    """

        df_cr_users = bq_client.query(sql_query).to_dataframe()

        # CR users with app_launch event and country and language data (LR stat)
        sql_query = f"""
                SELECT *
                    FROM `dataexploration-193817.user_data.cr_app_launch`
                WHERE
                    first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE() 
                """

        df_cr_app_launch = bq_client.query(sql_query).to_dataframe()

        # Eliminate duplicate cr users (multiple language combinations) - just keep the first one
        df_cr_app_launch = df_cr_app_launch.drop_duplicates(subset='user_pseudo_id',keep="first")
        
        #fix data typos
        df_cr_app_launch["app_language"] = df_cr_app_launch["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_cr_app_launch["app_language"] = df_cr_app_launch["app_language"].replace(
            "malgache", "malagasy"
        )
        df_cr_users["app_language"] = df_cr_users["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_cr_users["app_language"] = df_cr_users["app_language"].replace(
            "malgache", "malagasy"
        )
        df_unity_users["app_language"] = df_unity_users["app_language"].replace(
            "ukranian", "ukrainian"
        )
        df_unity_users["app_language"] = df_unity_users["app_language"].replace(
            "malgache", "malagasy"
        )

        max_level_indices = df_cr_users.groupby('user_pseudo_id')['max_user_level'].idxmax()
        df_cr_users = df_cr_users.loc[max_level_indices].reset_index()

        max_level_indices = df_unity_users.groupby('user_pseudo_id')['max_user_level'].idxmax()
        df_unity_users = df_unity_users.loc[max_level_indices].reset_index()

    logging.debug(p.print())
    return df_cr_users, df_unity_users, df_cr_first_open, df_cr_app_launch


@st.cache_data(ttl="1d", show_spinner=False)
def get_language_list():
    lang_list = ["All"]
    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
        sql_query = f"""
                    SELECT display_language
                    FROM `dataexploration-193817.user_data.language_max_level`
                    ;
                    """
        rows_raw = bq_client.query(sql_query)
        rows = [dict(row) for row in rows_raw]
        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df.drop_duplicates(inplace=True)
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


@st.cache_data(ttl="1d", show_spinner=False)
def get_app_version_list():
    app_versions = []
    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
        sql_query = f"""
                    SELECT *
                    FROM `dataexploration-193817.user_data.cr_app_versions`
                    """
        rows_raw = bq_client.query(sql_query)
        rows = [dict(row) for row in rows_raw]
        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        conditions = [
            f"app_version >=  'v1.0.25'",
        ]
        query = " and ".join(conditions)
        df = df.query(query)

        app_versions = np.array(df.values).flatten().tolist()
        app_versions.insert(0, "All")

    return app_versions