import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np
from pyinstrument import Profiler
import logging
import asyncio

# How far back to obtain user data.  Currently the queries pull back to 01/01/2021
start_date = "2021/01/01"

# Firebase returns two different formats of user_pseudo_id between
# web app events and android events, so we have to run multiple queries
# instead of a join because we don't have a unique key for both
# This would all be unncessery if dev had included the app user id per the spec.


import logging
import streamlit as st

async def get_users_list():
    p = Profiler(async_mode="disabled")
    with p:

        bq_client = st.session_state.bq_client

        # Helper function to run BigQuery in a thread
        async def run_query(query):
            return await asyncio.to_thread(bq_client.query(query).to_dataframe)

        # Define the queries
        sql_unity_users = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.unity_user_progress_inc`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """
        
        sql_cr_users = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.cr_user_progress_inc`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """

        sql_cr_app_launch = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.cr_app_launch_inc`
            WHERE first_open BETWEEN PARSE_DATE('%Y/%m/%d','{start_date}') AND CURRENT_DATE()
        """

        # Run all the queries asynchronously
        df_unity_users, df_cr_users, df_cr_app_launch = await asyncio.gather(
            run_query(sql_unity_users),
            run_query(sql_cr_users),
            run_query(sql_cr_app_launch),
        )

        # Fix data typos
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

        # We have an unknown anomalie where users from FTM do not show up in the CR events.  We 
        # need to remove them so we have a true funnel.
        missing_users = df_cr_users[~df_cr_users["cr_user_id"].isin(df_cr_app_launch["cr_user_id"])]

        # Remove missing users from df_cr_users - NOTE: Same users with multiple country combinations
        # will still be in df_cr_app_launch 
        df_cr_users = df_cr_users[~df_cr_users["cr_user_id"].isin(missing_users["cr_user_id"])]

        df_cr_app_launch,df_cr_users = clean_cr_users_to_single_language(df_cr_app_launch,df_cr_users)

        #clean unity users to the one with the furthest progress
        max_level_indices_unity = df_unity_users.groupby('user_pseudo_id')['max_user_level'].idxmax()
        df_unity_users = df_unity_users.loc[max_level_indices_unity].reset_index()

    p.print(color="red")
    


    return df_cr_users, df_unity_users,  df_cr_app_launch


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


@st.cache_data(ttl="1d", show_spinner=False)
def get_funnel_snapshots(daterange,languages):

    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
    else:
        st.write ("No database connection")
        return

    languages_str = ', '.join([f"'{lang}'" for lang in languages])

    sql_query = f"""
            SELECT *
            FROM `dataexploration-193817.user_data.funnel_snapshots`
            WHERE language IN ({languages_str})
            AND
            DATE(date) BETWEEN '{daterange[0].strftime("%Y-%m-%d")}' AND '{daterange[1].strftime("%Y-%m-%d")}' ;

            """

    df = bq_client.query(sql_query).to_dataframe() 
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    return df

# Users who play multiple languages or have multiple countries are consolidated
# to a single entry based on which combination took them the furthest in the game.
# If its a tie, will take the first entry. The reference to duplicates are users
# with multiple entries because of variations in these combinations

@st.cache_data(ttl="1d", show_spinner=False)
def clean_cr_users_to_single_language(df_app_launch, df_cr_users):

    # ✅  Identify and remove all duplicates from df_app_launch, but SAVE them for later
    duplicate_user_ids = df_app_launch[df_app_launch.duplicated(subset='user_pseudo_id', keep=False)]
    df_app_launch = df_app_launch[~df_app_launch["cr_user_id"].isin(duplicate_user_ids["cr_user_id"])]

    # ✅  Get list of users that had duplicates
    unique_duplicate_ids = duplicate_user_ids['cr_user_id'].unique().tolist()

    # ✅  Define event ranking of the funnel
    event_order = ["download_completed", "tapped_start", "selected_level", "puzzle_completed", "level_completed"]
    event_rank = {event: rank for rank, event in enumerate(event_order)}

    # ✅  Ensure "furthest_event" has no missing values
    df_cr_users["furthest_event"] = df_cr_users["furthest_event"].fillna("unknown")
 
    # ✅ Map event to numeric rank
    df_cr_users["event_rank"] = df_cr_users["furthest_event"].map(event_rank)

    # ✅ Flag whether event is "level_completed" - this means we switch to level number to determine furthest progress
    df_cr_users["is_level_completed"] = df_cr_users["furthest_event"] == "level_completed"

    # ✅ Ensure a single row per user across country & language
    df_cr_users = df_cr_users.sort_values(["cr_user_id", "is_level_completed", "max_user_level", "event_rank"], 
                                          ascending=[True, False, False, False])

    df_cr_users = df_cr_users.drop_duplicates(subset=["cr_user_id"], keep="first")  # ✅ Keep only best progress row

    # ✅ Ensure every user in df_cr_users has a matching row in df_app_launch
    users_to_update = df_cr_users[["cr_user_id", "app_language", "country"]].merge(
        df_app_launch[["cr_user_id", "app_language", "country"]],
        on="cr_user_id",
        how="left",
        suffixes=("_cr", "_app")
    )

    # ✅ Find users where the `app_language` in df_app_launch does not match the selected best `app_language` from df_cr_users
    language_mismatch = users_to_update[users_to_update["app_language_cr"] != users_to_update["app_language_app"]]
    
    if not language_mismatch.empty:

        # ✅ Update df_app_launch to reflect the correct `app_language` from df_cr_users
        df_app_launch.loc[df_app_launch["cr_user_id"].isin(language_mismatch["cr_user_id"]), "app_language"] = \
            df_app_launch["cr_user_id"].map(df_cr_users.set_index("cr_user_id")["app_language"])

    # ✅ Ensure all users with duplicates exist in df_cr_users
    missing_users = set(unique_duplicate_ids) - set(df_cr_users["cr_user_id"])

    # ✅ Add back the correct user rows in df_app_launch, ensuring **matching language & country**
    users_to_add_back = duplicate_user_ids.merge(
        df_cr_users[["cr_user_id", "app_language", "country"]],
        on=["cr_user_id", "app_language", "country"],
        how="left"  
    )

    # ✅ Drop NaN values to ensure only valid rows are added back
    users_to_add_back = users_to_add_back.dropna(subset=["app_language"])

    # ✅ If any users are still missing, add a fallback row for them
    fallback_users = duplicate_user_ids[duplicate_user_ids["cr_user_id"].isin(missing_users)]
    fallback_users = fallback_users.drop_duplicates(subset="cr_user_id", keep="first")

    # Append the fallback users
    users_to_add_back = pd.concat([users_to_add_back, fallback_users])

    # ✅ Deduplicate to ensure only one row per cr_user_id is added back
    users_to_add_back = users_to_add_back.drop_duplicates(subset="cr_user_id", keep="first")

    # ✅ Restore users into df_app_launch
    df_app_launch = pd.concat([df_app_launch, users_to_add_back])

    # ✅ Ensure df_app_launch has only unique cr_user_id

    df_app_launch = df_app_launch.drop_duplicates(subset="cr_user_id", keep="first")

    return df_app_launch, df_cr_users

