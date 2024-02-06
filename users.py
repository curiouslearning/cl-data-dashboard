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
        SELECT
        user_pseudo_id,
        geo.country AS country,
        app_info.id AS app_id,
        CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
        FROM
        `ftm-b9d99.analytics_159643920.events_20*` AS A,
        UNNEST(event_params) AS event_params
        WHERE
        app_info.id = 'org.curiouslearning.container'
        AND event_params.value.string_value LIKE '%feedthemonster.curiouscontent.org%'
        AND event_name = 'app_launch'
        AND event_params.key = 'web_app_url'
        AND PARSE_DATE('%Y%m%d', event_date) BETWEEN '2021-01-01' AND CURRENT_DATE()
        GROUP BY
        user_pseudo_id,
        country,
        app_id,
        first_open
        """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]
    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    duplicates = (
        df[df.duplicated(subset=["user_pseudo_id"], keep=False)]
    ).reset_index()
    df_no_duplicates = df.drop_duplicates(
        subset=["user_pseudo_id"], keep=False
    ).reset_index()

    return df
