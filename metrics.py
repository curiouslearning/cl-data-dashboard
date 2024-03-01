import streamlit as st
from rich import print
import pandas as pd
import numpy as np
import settings
import datetime as dt
import users

min_date = dt.datetime(2021, 1, 1).date()
max_date = dt.date.today()


@st.cache_data(ttl="1d", show_spinner=False)
def get_ave_cost_per_action(daterange):
    df_all = st.session_state.df_all

    df = df_all.query(
        "@daterange[0] <= day <= @daterange[1] and mobile_app_install > 0"
    )

    total_downloads = df["mobile_app_install"].sum()
    total_cost = df["cost"].sum()

    if total_downloads > 0:
        return float(total_cost) / float(total_downloads)

    return 0


@st.cache_data(ttl="1d", show_spinner=False)
def get_google_conversions(daterange):
    df = st.session_state.df_goog_conversions

    df1 = df.query("@daterange[0] <= day <= @daterange[1]")
    total = df1["button_clicks"].sum()
    return total


@st.cache_data(ttl="1d", show_spinner=False)
def get_campaign_data_totals(daterange, source):
    df_all = st.session_state.df_all

    df = df_all.query("@daterange[0] <= day <= @daterange[1]  and source == @source")
    df = df.groupby("campaign_id", as_index=True).agg(
        {
            "campaign_name": "first",
            "country": "first",
            "campaign_start_date": "first",
            "campaign_end_date": "first",
            "mobile_app_install": "sum",
            "clicks": "sum",
            "reach": "first",
            "button_clicks": "sum",
            "cost": "sum",
            "cpc": "sum",
            "impressions": "sum",
        }
    )

    df.sort_values(by=["campaign_start_date"], ascending=False)

    return df


def get_download_totals(daterange):
    df_all = st.session_state.df_all
    df = df_all.query("@daterange[0] <= day <= @daterange[1]")
    total = df["mobile_app_install"].sum()

    return total


def get_totals_by_metric(daterange, countries_list, stat="LR"):
    df_user_list = filter_user_data(daterange, countries_list, stat)

    return len(df_user_list)


def filter_user_data(daterange, countries_list, stat="LR"):

    language = "All"
    app = "Both"
    if "df_lr" and "df_la" not in st.session_state:
        return pd.DataFrame()

    df_la = st.session_state.df_la
    df_lr = st.session_state.df_lr

    if "language" in st.session_state:
        language = st.session_state.language
    if "app" in st.session_state:
        app = st.session_state.app

    conditions = [
        f"@daterange[0] <= first_open <= @daterange[1]",
        f"country.isin(@countries_list)",
    ]
    if language != "All":
        conditions.append("app_language == @language")

    if app == "CR":
        conditions.append("app_id == 'org.curiouslearning.container'")
    elif app == "Unity":
        conditions.append("app_id != 'org.curiouslearning.container'")

    if stat == "LA":
        conditions.append("max_user_level >= 1")

    query = " and ".join(conditions)

    if stat == "LA":
        df_user_list = df_la.query(query)
    else:
        df_user_list = df_lr.query(query)
    return df_user_list


def get_GPC_avg(daterange, countries_list):
    # Use LA as the baseline
    df_user_list = filter_user_data(daterange, countries_list, stat="LA")
    df_user_list = df_user_list.fillna(0)

    return 0 if len(df_user_list) == 0 else np.average(df_user_list.gpc)


def get_GC_avg(daterange, countries_list):
    # Use LA as the baseline
    df_user_list = filter_user_data(daterange, countries_list, stat="LA")
    df_user_list = df_user_list.fillna(0)

    cohort_count = len(df_user_list)
    gc_count = df_user_list[(df_user_list["gpc"] >= 90)].shape[0]

    return 0 if cohort_count == 0 else gc_count / cohort_count * 100


def get_country_counts(daterange, countries_list, stat):

    logger = settings.get_logger()
    if stat == "LA" or stat == "LR":
        df_lr = filter_user_data(daterange, countries_list, "LR")
        df_la = filter_user_data(daterange, countries_list, "LA")
        country_counts = (
            df_lr.groupby("country")
            .size()
            .to_frame(name="LR")
            .reset_index()
            .sort_values(by=stat, ascending=False)
            .merge(
                df_la.groupby("country").size().to_frame(name="LA").reset_index(),
                on="country",
                how="left",
            )
            .fillna(0)
        )
    elif stat == "GPC":
        df = filter_user_data(daterange, countries_list, stat="LA")
        # Calculate the average GPC per country
        avg_gpc_per_country = df.groupby("country")["gpc"].mean().round(2)
        # Create a new DataFrame with the average GPC per country
        country_counts = (
            pd.DataFrame(
                {
                    "country": avg_gpc_per_country.index,
                    "GPC": avg_gpc_per_country.values,
                }
            )
            .sort_values(by="GPC", ascending=False)
            .fillna(0)
        )

    else:
        df = filter_user_data(daterange, countries_list, stat="LA")
        gpc_gt_90_counts = (
            df[df["gpc"] >= 90].groupby("country")["user_pseudo_id"].count()
        )
        total_user_counts = df.groupby("country")["user_pseudo_id"].count()

        # Reset index to bring "country" back as a column
        gpc_gt_90_counts = gpc_gt_90_counts.reset_index()
        total_user_counts = total_user_counts.reset_index()

        # Merge the counts into a single DataFrame
        country_counts = pd.merge(
            gpc_gt_90_counts.rename(columns={"user_pseudo_id": "gpc_gt_90_users"}),
            total_user_counts.rename(columns={"user_pseudo_id": "total_users"}),
            on="country",
        )

        # Calculate the percentage and add it as a new column
        country_counts["GCA"] = (
            country_counts["gpc_gt_90_users"] / country_counts["total_users"] * 100
        )
        country_counts.sort_values(by="GCA", ascending=False, inplace=True)

    return country_counts


def get_total_installs():
    df_pd = st.session_state.df_pd

    return df_pd["Daily_Device_Installs"].sum()


@st.cache_data(ttl="1d", show_spinner=False)
def get_puzzle_completed_count():

    if "bq_client" in st.session_state:
        bq_client = st.session_state.bq_client
    sql_query = f"""
        select count(*) 
        FROM `dataexploration-193817.user_data.puzzle_completed_users`
        """

    iterator = bq_client.query(sql_query).result()
    first_row = next(iterator)
    return first_row[0]
