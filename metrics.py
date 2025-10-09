import streamlit as st
from rich import print
import pandas as pd
import numpy as np
import datetime as dt
import users

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]

def get_totals_by_metric(
    daterange=default_daterange,
    countries_list=[],
    stat="LR",
    cr_app_versions="All",
    app="CR",
    language="All",
    user_list=None 
):

    # if no list passed in then get the full list
    if len(countries_list) == 0:
        countries_list = users.get_country_list()

    df_user_list = filter_user_data(
        daterange=daterange, countries_list=countries_list, stat=stat, app=app, cr_app_versions=cr_app_versions, language=language,user_list=user_list
    )
    
    if (len(df_user_list) > 0):

        if stat not in ["DC", "TS", "SL", "PC", "LA"]:
            return len(df_user_list) #All LR 
        else:
            download_completed_count = len(
                df_user_list[df_user_list["furthest_event"] == "download_completed"]
            )

            tapped_start_count = len(
                df_user_list[df_user_list["furthest_event"] == "tapped_start"]
            )
            selected_level_count = len(
                df_user_list[df_user_list["furthest_event"] == "selected_level"]
            )
            puzzle_completed_count = len(
                df_user_list[df_user_list["furthest_event"] == "puzzle_completed"]
            )
            level_completed_count = len(
                df_user_list[df_user_list["furthest_event"] == "level_completed"]
            )

            if stat == "DC":
                return (
                    download_completed_count
                    + tapped_start_count
                    + selected_level_count
                    + puzzle_completed_count
                    + level_completed_count
                )

            if stat == "TS":
                return (
                    tapped_start_count
                    + selected_level_count
                    + puzzle_completed_count
                    + level_completed_count
                )

            if stat == "SL":  # all PC and SL users implicitly imply those events
                return selected_level_count + puzzle_completed_count + level_completed_count

            if stat == "PC":
                return puzzle_completed_count + level_completed_count

            if stat == "LA":
                return level_completed_count
    else:
        return 0

# Takes the complete user lists (cr_user_id) and filters based on input data, and returns
# a new filtered dataset
def filter_user_data(
    daterange=default_daterange,
    countries_list=["All"],
    cr_app_versions=["All"],
    stat="LR",
    app="CR",
    language=["All"],
    user_list=None,
    offline_filter=None
):
    
    #default column to filter user cohort list
    user_list_key = "cr_user_id"
    # Check if necessary dataframes are available
    if not all(key in st.session_state for key in ["df_cr_users", "df_unity_users",  "df_cr_app_launch"]):
        print("PROBLEM!")
        return pd.DataFrame()

    # Select the appropriate dataframe based on app and stat
    if app == "Unity":
        df = st.session_state.df_unity_users #Unity users are in one table only
        user_list_key = "user_pseudo_id"       
    elif app == "StandAloneHindi":
        df = st.session_state.df_cr_users
        df.to_csv("df.csv")
        df = (df[df["app"] == "StandAloneHindi"])
    elif app == "CR" and stat == "LR":
        df = st.session_state.df_cr_app_launch
    else:
        df = st.session_state.df_cr_users


    # Initialize a boolean mask
    mask = (
        df["first_open"] >= pd.to_datetime(daterange[0])
    ) & (
        df["first_open"] <= pd.to_datetime(daterange[1])
    )


    if "All" not in cr_app_versions and app == "CR":
        mask &= df["app_version"].isin(cr_app_versions)
    # Apply country filter if not "All"
    if countries_list[0] != "All":
        mask &= df['country'].isin(set(countries_list))

    # Apply language filter if not "All" 
    if language[0] != "All":
        mask &= df['app_language'].isin(set(language))
        
    # Apply started_in_offline_mode filter if not None
    if offline_filter is not None:
        if offline_filter is True:
            mask &= df["started_in_offline_mode"] == True
        else:  # offline_filter is False
            mask &= df["started_in_offline_mode"] != True

    # Apply stat-specific filters
    if stat == "LA":
        mask &= (df['max_user_level'] >= 1)
    elif stat == "RA":
        mask &= (df['max_user_level'] >= 25)
    elif stat == "GC":  # Game completed
        mask &= (df['max_user_level'] >= 1) & (df['gpc'] >= 90)
    elif stat == "LR":
        # No additional filters for these stats beyond daterange and optional countries/language
        pass
    
    # Filter the dataframe with the combined mask
    df = df.loc[mask]

    #If user list subset was passed in, filter on that as well
    if user_list is not None:

        if len(user_list) == 0:
            return pd.DataFrame()  # No matches — return empty

        df = df[df[user_list_key].isin(user_list)]

    return df


@st.cache_data(ttl="1d", show_spinner=False)
def get_date_cohort_dataframe(
    daterange=default_daterange,
    languages=["All"],
    countries_list=["All"],
    app="CR"):
    
    """
    Returns a DataFrame of activity for all users who first opened the app in the selected cohort.
    Useful for tracking how cohorts evolve over time.
    """

    # Get all of the users in the user selected window - this is the cohort
    df_user_cohort = filter_user_data(daterange=daterange,countries_list=countries_list,app="CR",language=languages)

    # All we need is their cr_user_id
    user_cohort_list = df_user_cohort["cr_user_id"]

    # Get superset of  the users up through today
    daterange = [daterange[0],dt.date.today()]
    df = filter_user_data(daterange=daterange,countries_list=countries_list,app=app,language=languages,user_list=user_cohort_list)
    
    return df

#@st.cache_data(ttl="1d", show_spinner=False)
def get_user_cohort_list(
    daterange=default_daterange,
    languages=["All"],
    cr_app_versions="All",
    countries_list=["All"],
    app="CR",
    as_list=True,
    offline_filter=None
):
    """
    Returns a list of user identifiers (default) or a DataFrame of cohort info based on first_open date,
    country, language, and app type. Use as_list=False to return full DataFrame.
    """
    df_user_cohort = filter_user_data(
        daterange=daterange,
        countries_list=countries_list,
        app=app,
        language=languages,
        cr_app_versions=cr_app_versions,
        offline_filter=offline_filter
    )

    if app in ["CR", "StandAloneHindi"]:
        user_cohort_df = df_user_cohort[["cr_user_id", "first_open","country", "app_language", "app_version"]]
        user_id_col = "cr_user_id"
    else:
        user_cohort_df = df_user_cohort[["user_pseudo_id"]]
        user_id_col = "user_pseudo_id"

    if as_list:
        return user_cohort_df[user_id_col].dropna().tolist()
    else:
        return user_cohort_df


def get_filtered_cohort(app, daterange, language, countries_list):
    """Returns (user_cohort_df, user_cohort_df_LR) for app selection."""
    is_cr = (app == ["CR"] or app == "CR")
    user_cohort_df_LR = None
    session_df = select_user_dataframe(app=app)
    user_cohort_df = get_user_cohort_df(
        session_df=session_df,
        daterange=daterange,
        languages=language,
        countries_list=countries_list,
        app=app
    )
    if is_cr:
        session_df_LR = select_user_dataframe(app=app, stat="LR")
        user_cohort_df_LR = get_user_cohort_df(
            session_df=session_df_LR,
            daterange=daterange,
            languages=language,
            countries_list=countries_list,
            app=app
        )
    return user_cohort_df, user_cohort_df_LR


def select_user_dataframe(app, stat=None):
    apps = [app] if isinstance(app, str) else app

    if "Unity" in apps:
        df = st.session_state.df_unity_users
        return df

    elif any(a.endswith("-standalone") for a in apps if isinstance(a, str)):
        df = st.session_state.df_cr_users
        if "All" not in apps:
            df = df[df["app"].isin(apps)]
        return df

    elif apps == ["CR"] and stat == "LR":
        df = st.session_state.df_cr_app_launch
        return df

    else:
        df = st.session_state.df_cr_users
        return df

def get_user_cohort_df(
    session_df,
    daterange=None,
    languages=["All"],
    countries_list=["All"],
    app=None,
):
    """
    Returns a DataFrame (all columns) for the cohort matching filters.
    - df: DataFrame to filter (already chosen by select_user_dataframe)
    - user_list_key: which column uniquely identifies users
    """
    cohort_df = session_df.copy()

    # Apply filters
    if daterange is not None and len(daterange) == 2:
        start = pd.to_datetime(daterange[0])
        end = pd.to_datetime(daterange[1])
        cohort_df = cohort_df[
        (cohort_df["first_open"] >= start) & (cohort_df["first_open"] <= end)
        ]

    if countries_list and countries_list != ["All"]:
        cohort_df = cohort_df[cohort_df["country"].isin(countries_list)]
        
    if languages and languages != ["All"]:
        lang_col = "app_language" if "app_language" in cohort_df.columns else "language"
        cohort_df = cohort_df[cohort_df[lang_col].isin(languages)]
        
    if app and app != ["All"] and "app" in cohort_df.columns:
        apps = [app] if isinstance(app, str) else app
        cohort_df = cohort_df[cohort_df["app"].isin(apps)]
        

    return cohort_df


@st.cache_data(ttl="1d", show_spinner=False)
def get_cohort_totals_by_metric(
    cohort_df,
    stat="LR"
):
    """
    Given a cohort_df (already filtered!), count users in each funnel stage or apply stat-specific filter.
    - cohort_df: DataFrame, filtered to your user cohort (one row per user)
    - stat: string, which funnel metric to count ("LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC")
    """

    # Stat-specific filters (formerly in filter_user_data)
    if stat == "LA":
        # Learners Acquired: max_user_level >= 1
        return (cohort_df['max_user_level'] >= 1).sum()
    elif stat == "RA":
        # Readers Acquired: max_user_level >= 25
        return (cohort_df['max_user_level'] >= 25).sum()
    elif stat == "GC":
        # Game Completed: max_user_level >= 1 AND gpc >= 90
        return ((cohort_df['max_user_level'] >= 1) & (cohort_df['gpc'] >= 90)).sum()
    elif stat == "LR":
        # Learner Reached: all users in cohort
        return len(cohort_df)

    # Otherwise: classic funnel by furthest_event
    furthest = cohort_df["furthest_event"]

    download_completed_count = (furthest == "download_completed").sum()
    tapped_start_count      = (furthest == "tapped_start").sum()
    selected_level_count    = (furthest == "selected_level").sum()
    puzzle_completed_count  = (furthest == "puzzle_completed").sum()
    level_completed_count   = (furthest == "level_completed").sum()

    if stat == "DC":
        return (
            download_completed_count
            + tapped_start_count
            + selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "TS":
        return (
            tapped_start_count
            + selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "SL":
        return (
            selected_level_count
            + puzzle_completed_count
            + level_completed_count
        )
    if stat == "PC":
        return (
            puzzle_completed_count
            + level_completed_count
        )

    return 0  # default fallback


@st.cache_data(ttl="1d", show_spinner=False)
def funnel_percent_by_group(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    min_funnel=False
):
    """
    Returns a single DataFrame with raw counts and percent-normalized columns (suffix '_pct') by group.
    Handles CR (two dfs for LR), all other apps (one df for all steps).

    Adds:
        • GPP  - average game progress (mean gpc)
        • GCA  - % of LA users with gpc >= 90

    Special handling:
        If the dataframe lacks 'furthest_event' (e.g., CR app_launch dataset used for LR),
        returns only LR counts by group and skips full funnel expansion.
    """

    app_name = app[0] if isinstance(app, list) and len(app) > 0 else app
    app_name = str(app_name) if app_name is not None else ""

    user_key = "cr_user_id"
    funnel_steps = ["LR", "PC", "LA", "RA", "GC"]

    if app_name == "CR" and not min_funnel:
        funnel_steps = ["LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC"]
    elif app_name == "Unity":
        user_key = "user_pseudo_id"

    # ✅ Short-circuit: handle datasets without furthest_event (e.g., CR app_launch / LR)
    if "furthest_event" not in cohort_df.columns:
        df = (
            cohort_df.groupby(groupby_col, dropna=False)
            .agg({user_key: "nunique"})
            .reset_index()
            .rename(columns={user_key: "LR"})
        )
        df["LR_pct"] = 100.0
        return df, ["LR"]

    # --- Normal funnel logic ---
    group_vals = set(cohort_df[groupby_col].dropna().unique())
    if cohort_df_LR is not None:
        group_vals |= set(cohort_df_LR[groupby_col].dropna().unique())

    records = []
    for group in sorted(group_vals):
        # LR count (special handling for CR with separate LR df)
        if app_name == "CR" and cohort_df_LR is not None:
            group_LR = cohort_df_LR[cohort_df_LR[groupby_col] == group]
            count_LR = (
                group_LR[user_key].nunique() if user_key in group_LR else len(group_LR)
            )
        else:
            group_LR = cohort_df[cohort_df[groupby_col] == group]
            count_LR = (
                group_LR[user_key].nunique() if user_key in group_LR else len(group_LR)
            )

        row = {groupby_col: group, "LR": count_LR}
        group_df = cohort_df[cohort_df[groupby_col] == group]

        for step in funnel_steps[1:]:
            row[step] = get_cohort_totals_by_metric(group_df, stat=step)

        records.append(row)

    df = pd.DataFrame(records)

    # --- Percent-normalized columns ---
    norm_steps = [s for s in funnel_steps if s != "LR"]
    for step in funnel_steps:
        if step == "LR":
            df[f"{step}_pct"] = 100.0
        else:
            df[f"{step}_pct"] = df[step] / df["LR"] * 100

    # --- Drop rows where all post-LR steps are zero (optional) ---
    all_zero = (df[norm_steps].fillna(0).astype(float) == 0).all(axis=1)
    df = df[~all_zero].reset_index(drop=True)

    # --- Add GPP and GCA if gpc exists ---
    if "gpc" in cohort_df.columns:
        la_df = cohort_df[cohort_df["max_user_level"] >= 1].copy()

        # GPP = average gpc among LA users
        gpp = (
            la_df.groupby(groupby_col)["gpc"]
            .mean()
            .reset_index(name="GPP")
            .fillna(0)
        )
        df = df.merge(gpp, on=groupby_col, how="left")
        df["GPP_pct"] = df["GPP"]  # maintain consistent suffix pattern

        # GCA = % of LA users with gpc >= 90
        total_counts = (
            la_df.groupby(groupby_col)[user_key]
            .nunique()
            .reset_index(name="LA_total")
        )
        gc_counts = (
            la_df[la_df["gpc"] >= 90]
            .groupby(groupby_col)[user_key]
            .nunique()
            .reset_index(name="GC_count")
        )
        gca = total_counts.merge(gc_counts, on=groupby_col, how="left").fillna(0)
        gca["GCA"] = (gca["GC_count"] / gca["LA_total"] * 100).round(2)
        df = df.merge(gca[[groupby_col, "GCA"]], on=groupby_col, how="left")
        df["GCA_pct"] = df["GCA"]

        # Extend funnel_steps for downstream charts/tables
        funnel_steps = funnel_steps + ["GPP", "GCA"]

    return df, funnel_steps

@st.cache_data(ttl="1d", show_spinner=False)
def get_sorted_funnel_df(
    cohort_df,
    cohort_df_LR=None,
    groupby_col="app_language",
    app=None,
    min_funnel=True,
    stat="LA",
    sort_by="Total",
    ascending=False,
    use_top_ten=True
):
    """
    Returns a funnel dataframe (with counts and percentages) sorted by the chosen stat.
    Works for both funnel metrics (LR→GC) and performance metrics (GPP, GCA).

    Parameters
    ----------
    cohort_df : pd.DataFrame
        Main cohort dataframe (includes all funnel users)
    cohort_df_LR : pd.DataFrame, optional
        Learners Reached dataframe (for CR app only)
    groupby_col : str, default "app_language"
        Column to group by ("app_language", "country", etc.)
    app : str or list, optional
        App name (e.g., "CR", "Unity", etc.)
    min_funnel : bool, default True
        If True, uses minimal funnel steps for CR
    stat : str, default "LA"
        Funnel metric to sort by ("LR", "LA", "RA", "GC", "GPP", "GCA", etc.)
    sort_by : str, default "Total"
        Whether to sort by "Total" (raw counts) or "Percent"
    ascending : bool, default False
        Sort ascending (lowest first) or descending (highest first)
    use_top_ten : bool, default True
        If True, return top 10 rows

    Returns
    -------
    df : pd.DataFrame
        Sorted funnel dataframe with all steps and derived metrics
    funnel_steps : list
        Ordered list of funnel step names
    """

    # --- Compute the funnel + percentages ---
    df, funnel_steps = funnel_percent_by_group(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel
    )

    # --- Normalize the metric name (case-insensitive) ---
    stat = stat.upper().strip()

    # --- Special handling for derived metrics ---
    derived_metrics = ["GPP", "GCA"]
    if stat in derived_metrics:
        # These are already in percentage units and do not have raw count variants
        sort_col = stat
    else:
        # Pick between raw count or percent column
        if sort_by.lower() == "percent":
            sort_col = stat if stat == "LR" else f"{stat}_pct"
        else:
            sort_col = stat

    # --- Validate column existence ---
    if sort_col not in df.columns:
        raise KeyError(
            f"Column '{sort_col}' not found in funnel dataframe. "
            f"Available columns: {list(df.columns)}"
        )

    # --- Sort and optionally limit to top 10 ---
    df = df.sort_values(by=sort_col, ascending=ascending)
    if use_top_ten:
        df = df.head(10)

    return df, funnel_steps
