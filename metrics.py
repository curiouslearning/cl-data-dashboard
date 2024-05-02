import streamlit as st
from rich import print
import pandas as pd
import numpy as np
import datetime as dt
import users


@st.cache_data(ttl="1d", show_spinner=False)
def get_ave_cost_per_action(daterange):
    df_campaigns = st.session_state.df_campaigns

    df = df_campaigns.query(
        "@daterange[0] <= day <= @daterange[1] and mobile_app_install > 0"
    )

    total_downloads = df["mobile_app_install"].sum()
    total_cost = df["cost"].sum()

    if total_downloads > 0:
        return float(total_cost) / float(total_downloads)

    return 0


def get_download_totals():
    df_campaigns = st.session_state.df_campaigns
    total_fb = df_campaigns["mobile_app_install"].sum()

    total_goog = df_campaigns["button_clicks"].sum()

    return total_fb, total_goog


def get_totals_by_metric(
    daterange=[dt.datetime(2021, 1, 1).date(), dt.date.today()],
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
    daterange=[],
    countries_list=[],
    stat="LR",
    cr_app_version="All",
    app="Both",
    language="All",
):

    if "df_user_list" and "df_first_open" not in st.session_state:
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

    if language != "All":
        conditions.append("app_language == @language")

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

    if stat == "PC":
        conditions.append(
            "(furthest_event == 'puzzle_completed' or furthest_event == 'level_completed' )"
        )

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


# Returns a DataFrame list of countries and the number of users per country
@st.cache_data(ttl="1d", show_spinner=False)
def get_country_counts(daterange, countries_list, app="Both", language="All"):

    dfLR = (
        filter_user_data(daterange, countries_list, "LR", app=app, language=language)
        .groupby("country")
        .size()
        .to_frame(name="LR")
        .reset_index()
    )
    dfLA = (
        filter_user_data(daterange, countries_list, "LA", app=app, language=language)
        .groupby("country")
        .size()
        .to_frame(name="LA")
        .reset_index()
    )
    country_counts = dfLR.merge(dfLA, on="country", how="left").fillna(0)

    #### GPP ###
    df = filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    avg_gpc_per_country = df.groupby("country")["gpc"].mean().round(2)
    dfGPP = pd.DataFrame(
        {
            "country": avg_gpc_per_country.index,
            "GPP": avg_gpc_per_country.values,
        }
    ).fillna(0)

    country_counts = country_counts.merge(dfGPP, on="country", how="left").fillna(0)

    dfPC = (
        filter_user_data(daterange, countries_list, "PC", app=app, language=language)
        .groupby("country")
        .size()
        .to_frame(name="PC")
        .reset_index()
    )

    country_counts = country_counts.merge(dfPC, on="country", how="left").fillna(0)
    df = filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    gpc_gt_90_counts = df[df["gpc"] >= 90].groupby("country")["user_pseudo_id"].count()
    total_user_counts = df.groupby("country")["user_pseudo_id"].count()

    # Reset index to bring "country" back as a column
    gpc_gt_90_counts = gpc_gt_90_counts.reset_index()
    total_user_counts = total_user_counts.reset_index()

    # Merge the counts into a single DataFrame
    gca = pd.merge(
        gpc_gt_90_counts.rename(columns={"user_pseudo_id": "gpc_gt_90_users"}),
        total_user_counts.rename(columns={"user_pseudo_id": "total_users"}),
        on="country",
    )

    # Calculate the percentage and add it as a new column
    gca["GCA"] = gca["gpc_gt_90_users"] / gca["total_users"] * 100
    country_counts = (
        country_counts.merge(gca, on="country", how="left").round(2).fillna(0)
    )
    return country_counts
