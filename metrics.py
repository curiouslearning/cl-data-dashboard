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
    app="Both",
    language="All",
):

    # if no list passed in then get the full list
    if len(countries_list) == 0:
        countries_list = users.get_country_list()

    df_user_list = filter_user_data(
        daterange, countries_list, stat, cr_app_versions, app=app, language=language
    )

    if stat not in ["DC", "TS", "SL", "PC", "LA"]:
        return len(df_user_list) #All LR or FO
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
            return tapped_start_count + puzzle_completed_count + level_completed_count

        if stat == "PC":
            return puzzle_completed_count + level_completed_count

        if stat == "LA":
            return level_completed_count


# Takes the complete user lists and filters based on input data, and returns
# a new filtered dataset

def filter_user_data(
    daterange=default_daterange,
    countries_list=["All"],
    stat="LR",
    cr_app_versions="All",
    app="Both",
    language=["All"],
):
    # Check if necessary dataframes are available
    if not all(key in st.session_state for key in ["df_cr_users", "df_unity_users", "df_cr_first_open", "df_cr_app_launch"]):
        print("PROBLEM!")
        return pd.DataFrame()

    # Select the appropriate dataframe based on app and stat
    if app == "Unity":
        df = st.session_state.df_unity_users #Unity users are in one table only
    elif app == "Both" and stat == "LR":
        df1 = st.session_state.df_unity_users
        df2 = st.session_state.df_cr_app_launch
        df =  pd.concat([df1, df2], axis=0)
    elif app == "Both" and stat != "LR":
        df1 = st.session_state.df_unity_users
        df2 = st.session_state.df_cr_users
        df =  pd.concat([df1, df2], axis=0)
    elif app == "CR" and stat == "LR":
        df = st.session_state.df_cr_app_launch
    elif app == "CR" and stat == "FO":
        df = st.session_state.df_cr_first_open
    else:
        df = st.session_state.df_cr_users

    # Initialize a boolean mask
    mask = (df['first_open'] >= daterange[0]) & (df['first_open'] <= daterange[1])

    # Apply country filter if not "All"
    if countries_list[0] != "All":
        mask &= df['country'].isin(set(countries_list))

    # Apply language filter if not "All" and stat is not "FO"
    if language[0] != "All" and stat != "FO":
        mask &= df['app_language'].isin(set(language))

    # Apply stat-specific filters
    if stat == "LA":
        mask &= (df['max_user_level'] >= 1)
    elif stat == "RA":
        mask &= (df['max_user_level'] >= 25)
    elif stat == "GC":  # Game completed
        mask &= (df['max_user_level'] >= 1) & (df['gpc'] >= 90)
    elif stat == "LR" or stat == "FO":
        # No additional filters for these stats beyond daterange and optional countries/language
        pass
    
    # Filter the dataframe with the combined mask
    df = df.loc[mask]

    return df


# Average Game Progress Percent
def get_GPP_avg(daterange, countries_list, app="Both", language="All"):
    # Use LA as the baseline
    df_user_list = filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    df_user_list = df_user_list.fillna(0)

    return 0 if len(df_user_list) == 0 else np.average(df_user_list.gpc)


# Average Game Complete
def get_GC_avg(daterange, countries_list, app="Both", language="All"):
    # Use LA as the baseline
    df_user_list = filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    df_user_list = df_user_list.fillna(0)

    cohort_count = len(df_user_list)
    gc_count = df_user_list[(df_user_list["gpc"] >= 90)].shape[0]

    return 0 if cohort_count == 0 else gc_count / cohort_count * 100


def weeks_since(daterange):
    current_date = dt.datetime.now()
    daterange_datetime = dt.datetime.combine(daterange[0], dt.datetime.min.time())

    difference = current_date - daterange_datetime

    return difference.days // 7


# Returns a DataFrame list of counts by language or counts by country
@st.cache_data(ttl="1d", show_spinner=False)
def get_counts(
    type="app_language",
    daterange=default_daterange,
    countries_list=["All"],
    app="Both",
    language=["All"],
):
    dfLR = (
        filter_user_data(
            daterange, countries_list, stat="LR", app=app, language=language
        )
        .groupby(type)
        .size()
        .to_frame(name="LR")
        .reset_index()
    )
    dfLA = (
        filter_user_data(daterange, countries_list, "LA", app=app, language=language)
        .groupby(type)
        .size()
        .to_frame(name="LA")
        .reset_index()
    )
    counts = dfLR.merge(dfLA, on=type, how="left").fillna(0)

    #### GPP ###
    df = filter_user_data(
       daterange, countries_list, stat="LA", app=app, language=language
       )
    avg_gpc_per_type = df.groupby(type)["gpc"].mean().round(2)
    dfGPP = pd.DataFrame(
          {
              type: avg_gpc_per_type.index,
             "GPP": avg_gpc_per_type.values,
            }
    ).fillna(0)

    counts = counts.merge(dfGPP, on=type, how="left").fillna(0)

    dfPC = (
        filter_user_data(daterange, countries_list, "PC", app=app, language=language)
        .groupby(type)
        .size()
        .to_frame(name="PC")
        .reset_index()
    )

    counts = counts.merge(dfPC, on=type, how="left").fillna(0)
    df = filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    gpc_gt_90_counts = df[df["gpc"] >= 90].groupby(type)["user_pseudo_id"].count()
    total_user_counts = df.groupby(type)["user_pseudo_id"].count()

    # Reset index to bring "country" back as a column
    gpc_gt_90_counts = gpc_gt_90_counts.reset_index()
    total_user_counts = total_user_counts.reset_index()

    # Merge the counts into a single DataFrame
    gca = pd.merge(
        gpc_gt_90_counts.rename(columns={"user_pseudo_id": "gpc_gt_90_users"}),
        total_user_counts.rename(columns={"user_pseudo_id": "total_users"}),
        on=type,
    )

    # Calculate the percentage and add it as a new column
    gca["GCA"] = gca["gpc_gt_90_users"] / gca["total_users"] * 100
    counts = counts.merge(gca, on=type, how="left").round(2).fillna(0)
    return counts


@st.cache_data(ttl="1d", show_spinner=False)
def build_funnel_dataframe(
    index_col="language",
    daterange=default_daterange,
    languages=["All"],
    countries_list=["All"],
):
    df = pd.DataFrame(columns=[index_col, "LR", "DC", "TS", "SL", "PC", "RA", "LA"])
    if index_col == "start_date":
        weeks = weeks_since(daterange)
        iteration = range(1, weeks + 1)
    elif index_col == "language":
        iteration = languages

    results = []

    for i in iteration:
        if index_col == "language":
            language = [i]
        else:
            language = languages
            end_date = dt.datetime.now().date()
            start_date = dt.datetime.now().date() - dt.timedelta(i * 7)
            daterange = [start_date, end_date]

        DC = get_totals_by_metric(
            daterange,
            stat="DC",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        SL = get_totals_by_metric(
            daterange,
            stat="SL",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        TS = get_totals_by_metric(
            daterange,
            stat="TS",
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        PC = get_totals_by_metric(
            daterange,
            stat="PC",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LA = get_totals_by_metric(
            daterange,
            stat="LA",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LR = get_totals_by_metric(
            daterange,
            stat="LR",
            language=language,
            countries_list=countries_list,
            app="CR",
        )        
        RA = get_totals_by_metric(
            daterange,
            stat="RA",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        GC = get_totals_by_metric(
            daterange,
            stat="GC",
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        entry = {
            "LR": LR,
            "DC": DC,
            "TS": TS,
            "SL": SL,
            "PC": PC,
            "LA": LA,
            "RA": RA,
            "GC": GC,
        }

        if index_col == "language":
            entry["language"] = language[0]
        else:
            entry["start_date"] = start_date

        results.append(entry)

    df = pd.DataFrame(results)

    return df

def add_level_percents(df):

    try:
        df["DC over LR"] = np.where(df["LR"] == 0, 0, (df["DC"] / df["LR"]) * 100)
        df["DC over LR"] = df["DC over LR"].astype(int)
    except ZeroDivisionError:
        df["DC over LR"] = 0

    try:
        df["TS over LR"] = np.where(df["LR"] == 0, 0, (df["TS"] / df["LR"]) * 100)
        df["TS over LR"] = df["TS over LR"].astype(int)
    except ZeroDivisionError:
        df["TS over LR"] = 0

    try:
        df["TS over DC"] = np.where(df["DC"] == 0, 0, (df["TS"] / df["DC"]) * 100)
        df["TS over DC"] = df["TS over DC"].astype(int)
    except ZeroDivisionError:
        df["TS over DC"] = 0

    try:
        df["SL over LR"] = np.where(df["LR"] == 0, 0, (df["SL"] / df["LR"]) * 100)
        df["SL over LR"] = df["SL over LR"].astype(int)
    except ZeroDivisionError:
        df["SL over LR"] = 0

    try:
        df["SL over TS"] = np.where(df["TS"] == 0, 0, (df["SL"] / df["TS"]) * 100)
        df["SL over TS"] = df["SL over TS"].astype(int)
    except ZeroDivisionError:
        df["SL over TS"] = 0

    try:
        df["PC over LR"] = np.where(df["LR"] == 0, 0, (df["PC"] / df["LR"]) * 100)
        df["PC over LR"] = df["PC over LR"].astype(int)
    except ZeroDivisionError:
        df["PC over LR"] = 0

    try:
        df["RA over LR"] = np.where(df["LR"] == 0, 0, (df["RA"] / df["LR"]) * 100)
        df["RA over LR"] = df["RA over LR"].astype(int)
    except ZeroDivisionError:
        df["RA over LR"] = 0
    try:
        df["RA over LA"] = np.where(df["LA"] == 0, 0, (df["RA"] / df["LA"]) * 100)
        df["RA over LA"] = df["RA over LA"].astype(int)
    except ZeroDivisionError:
        df["RA over LA"] = 0

    try:
        df["PC over SL"] = np.where(df["SL"] == 0, 0, (df["PC"] / df["SL"]) * 100)
        df["PC over SL"] = df["PC over SL"].astype(int)
    except ZeroDivisionError:
        df["PC over SL"] = 0

    try:
        df["LA over LR"] = np.where(df["LR"] == 0, 0, (df["LA"] / df["LR"]) * 100)
        df["LA over LR"] = df["LA over LR"].astype(int)
    except ZeroDivisionError:
        df["LA over LR"] = 0

    try:
        df["LA over PC"] = np.where(df["PC"] == 0, 0, (df["LA"] / df["PC"]) * 100)
        df["LA over PC"] = df["LA over PC"].astype(int)
    except ZeroDivisionError:
        df["LA over PC"] = 0

    try:
        df["GC over LR"] = np.where(df["LR"] == 0, 0, (df["GC"] / df["LR"]) * 100)
        df["GC over LR"] = df["GC over LR"].astype(int)
    except ZeroDivisionError:
        df["GC over LR"] = 0

    try:
        df["GC over RA"] = np.where(df["RA"] == 0, 0, (df["GC"] / df["RA"]) * 100)
        df["GC over RA"] = df["GC over RA"].astype(int)
    except ZeroDivisionError:
        df["GC over RA"] = 0
        
    return df


# Get the campaign data and filter by date, language, and country selections
def filter_campaigns(df_campaigns_all,daterange,selected_languages,countries_list):

    # Drop the campaigns that don't meet the naming convention
    condition = (df_campaigns_all["app_language"].isna()) | (df_campaigns_all["country"].isna())
    df_campaigns = df_campaigns_all[~condition]

    mask = (df_campaigns['segment_date'].dt.date >= daterange[0]) & (df_campaigns['segment_date'].dt.date <= daterange[1])
    df_campaigns = df_campaigns.loc[mask]
    # Apply country filter if not "All"

    if countries_list[0] != "All":
      mask &= df_campaigns['country'].isin(set(countries_list))

    # Apply language filter if not "All" and stat is not "FO"
    if selected_languages[0] != "All" :
        mask &= df_campaigns['app_language'].isin(set(selected_languages))

    df_campaigns = df_campaigns.loc[mask]

    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    return df_campaigns


def get_month_ranges(start_date, end_date):
    # This function returns a list of start and end dates for each month in the range
    month_ranges = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        next_month = current_date.replace(day=28) + dt.timedelta(days=4)  # This will get you to the next month
        month_end = min(end_date, next_month.replace(day=1) - dt.timedelta(days=1))  # End of the current month
        month_ranges.append((current_date, month_end))
        current_date = next_month.replace(day=1)  # Move to the first day of the next month
    
    return month_ranges

#Returns a dataframe of the totals of a stat for each month
def get_totals_per_month(daterange,stat,countries_list,language):

    #First get all campaign data
    df_campaigns_all = st.session_state["df_campaigns_all"]

    # Get the list of (start_date, end_date) tuples for each month
    month_ranges = get_month_ranges(daterange[0], daterange[1])

    # Initialize an empty list to store the results
    totals_by_month = []

    # Loop over each month and call the function
    for start_date, end_date in month_ranges:
        df_campaigns = df_campaigns_all
        daterange=[start_date, end_date]
        total = get_totals_by_metric(
            daterange=daterange, countries_list=countries_list,stat=stat, language=language
        )

        df_campaigns = filter_campaigns(df_campaigns,daterange,language,countries_list)

        cost = df_campaigns["cost"].sum()

        lrc = (cost / total).round(2) if total != 0 else 0

        # Store the total along with the month start
        totals_by_month.append({
            "month": start_date.strftime("%B-%Y"),  # Format the date as 'YYYY-MM' for the month
            "total": total,
            "cost": cost,
            "LRC": lrc
        })

    # Convert the results to a DataFrame
    df_totals = pd.DataFrame(totals_by_month)

    # Display the DataFrame
    return df_totals


