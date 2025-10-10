import streamlit as st
import pandas as pd
from rich import print as print
import numpy as np
import gcsfs
import settings


@st.cache_data(ttl="1d", show_spinner=False)
def load_parquet_from_gcs(file_pattern: str) -> pd.DataFrame:
    credentials, _ = settings.get_gcp_credentials()
    fs = gcsfs.GCSFileSystem(project="dataexploration-193817", token=credentials)
    files = fs.glob(file_pattern)

    if not files:
        raise FileNotFoundError(f"No files matching pattern: {file_pattern}")
    df = pd.read_parquet(files, filesystem=fs).copy()

    return df


def load_unity_user_progress_from_gcs():
    return load_parquet_from_gcs("user_data_parquet_cache/unity_user_progress_*.parquet")

def load_cr_user_progress_from_gcs():
    return load_parquet_from_gcs("user_data_parquet_cache/cr_user_progress_a*.parquet")

def load_cr_app_launch_from_gcs():
    return load_parquet_from_gcs("user_data_parquet_cache/cr_app_launch_*.parquet")


def ensure_user_data_initialized():
    import traceback
    """Run init_user_data once per session, with error handling."""
    if "user_data_initialized" not in st.session_state:
        try:
            init_user_data()
            st.session_state["user_data_initialized"] = True
        except Exception as e:
            st.error(f"❌ Failed to initialize user data: {e}")
            st.text(traceback.format_exc())
            st.stop()

def init_user_data():
    if st.session_state.get("user_data_initialized"):
        return  # already initialized this session
    with st.spinner("Loading User Data", show_time=True):
        from pyinstrument import Profiler
        from pyinstrument.renderers.console import ConsoleRenderer
        import settings

        profiler = Profiler(async_mode="disabled")
        with profiler:
            # Cached fast parquet loads
            df_cr_users = load_cr_user_progress_from_gcs()

            df_unity_users = load_unity_user_progress_from_gcs()
            df_cr_app_launch = load_cr_app_launch_from_gcs()

            # Validation
            if df_cr_users.empty or df_unity_users.empty or df_cr_app_launch.empty:
                raise ValueError("❌ One or more dataframes were empty after loading.")
            

            # Fix dates and clean
            df_cr_users = fix_date_columns(df_cr_users, ["first_open", "last_event_date"])
            df_unity_users = fix_date_columns(df_unity_users, ["first_open", "la_date", "last_event_date"])
            df_cr_app_launch = fix_date_columns(df_cr_app_launch, ["first_open"])

            max_level_indices = df_unity_users.groupby("user_pseudo_id")["max_user_level"].idxmax()
            df_unity_users = df_unity_users.loc[max_level_indices].reset_index(drop=True)

            df_cr_app_launch["app_language"] = clean_language_column(df_cr_app_launch)
            df_cr_users["app_language"] = clean_language_column(df_cr_users)

          #  missing_users = df_cr_users[~df_cr_users["cr_user_id"].isin(df_cr_app_launch["cr_user_id"])]
          #  df_cr_users = df_cr_users[~df_cr_users["cr_user_id"].isin(missing_users["cr_user_id"])]

            df_cr_app_launch, df_cr_users = clean_cr_users_to_single_language(df_cr_app_launch, df_cr_users)
            
            #active_span can be negative when users start the game in offline mode and have a first_open date later 
            # than last_event_date.  Set those to zero
            df_cr_users["active_span"] = df_cr_users["active_span"].clip(lower=0)
            
            # Assign to session state
            st.session_state["df_cr_users"] = df_cr_users
            st.session_state["df_unity_users"] = df_unity_users
            st.session_state["df_cr_app_launch"] = df_cr_app_launch
            st.session_state["user_data_initialized"] = True

        # Log the profile only once
        settings.get_logger().debug(
            profiler.output(ConsoleRenderer(show_all=False, timeline=True, color=True, unicode=True, short_mode=False))
        )

# Language cleanup
def clean_language_column(df):
    return df["app_language"].replace({
        "ukranian": "ukrainian",
        "malgache": "malagasy",
        "arabictest": "arabic",
        "farsitest": "farsi"
    })

@st.cache_data(ttl="1d", show_spinner=False)
def get_language_list():

    _, bq_client = settings.get_gcp_credentials()

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
    _, bq_client = settings.get_gcp_credentials()

    sql_query = f"""
                SELECT country
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
    
    # This is a fix for a nasty bug where a user can have a different first_open in one dataframe vs the other.
    # Its because cr_app_launch is Curious Reader first open but cr_user_progress is FTM first_open
    mask_cr = df_cr_users["app"] == "CR"
    df_cr_users.loc[mask_cr, "first_open"] = df_cr_users.loc[mask_cr, "cr_user_id"].map(
        df_app_launch.set_index("cr_user_id")["first_open"]
    )
    

    return df_app_launch, df_cr_users

@st.cache_data(ttl="1d", show_spinner=False)
def get_app_version_list():
    app_versions = []
    _, bq_client = settings.get_gcp_credentials()

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

def fix_date_columns(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
