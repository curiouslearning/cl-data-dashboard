import streamlit as st
from rich import print
import pandas as pd
import numpy as np
import datetime as dt
import users
import metrics

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]


def get_totals_by_metric(
    daterange=default_daterange,
    countries_list=[],
    stat="LR",
    cr_app_version="All",
    app="Both",
    language="All",
):

    # if no list passed in then get the full list
    if len(countries_list) == 0:
        countries_list = users.get_country_list()

    df_user_list = filter_user_data(
        daterange, countries_list, stat, cr_app_version, app=app, language=language
    )

    if stat not in ["DC", "TS", "SL", "PC", "LA"]:
        return len(df_user_list)
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
    cr_app_version="All",
    app="Both",
    language=["All"],
):
    if "df_user_list" and "df_first_open" not in st.session_state:
        print("PROBLEM!")
        return pd.DataFrame()

    df_user_list = st.session_state.df_user_list
    df_first_open = st.session_state.df_first_open

    conditions = [
        f"@daterange[0] <= first_open <= @daterange[1]",
    ]

    if stat == "LA":
        conditions.append("max_user_level >= 1")

    if countries_list[0] != "All":
        conditions.append(
            f"country.isin(@countries_list)",
        )
    if language[0] != "All":
        conditions.append(
            f"app_language.isin(@language)",
        )

    if app == "CR":
        conditions.append("app_id == 'org.curiouslearning.container'")
        if cr_app_version != "All":
            conditions.append("app_version == @cr_app_version")
    elif app == "Unity":
        conditions.append("app_id != 'org.curiouslearning.container'")

    if stat == "LR":
        query = " and ".join(conditions)
        df = df_first_open.query(query)
        return df

    if stat == "GC":  # game completed
        conditions.append("max_user_level >= 1")
        query = " and ".join(conditions)
        df = df_user_list.query(query)
        df = df[(df["gpc"] >= 90)]
        return df

    # All other stat options (LA)
    query = " and ".join(conditions)

    df = df_user_list.query(query)
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
    df = pd.DataFrame(columns=[index_col, "LR", "DC", "TS", "SL", "PC", "LA"])
    if index_col == "start_date":
        weeks = metrics.weeks_since(daterange)
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

        DC = metrics.get_totals_by_metric(
            daterange,
            stat="DC",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        SL = metrics.get_totals_by_metric(
            daterange,
            stat="SL",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        TS = metrics.get_totals_by_metric(
            daterange,
            stat="TS",
            language=language,
            countries_list=countries_list,
            app="CR",
        )

        PC = metrics.get_totals_by_metric(
            daterange,
            stat="PC",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LA = metrics.get_totals_by_metric(
            daterange,
            stat="LA",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        LR = metrics.get_totals_by_metric(
            daterange,
            stat="LR",
            language=language,
            countries_list=countries_list,
            app="CR",
        )
        GC = metrics.get_totals_by_metric(
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
        df["GC over LA"] = np.where(df["LA"] == 0, 0, (df["GC"] / df["LA"]) * 100)
        df["GC over LA"] = df["GC over LA"].astype(int)
    except ZeroDivisionError:
        df["GC over LA"] = 0
        
    return df