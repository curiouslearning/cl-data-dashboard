import streamlit as st
from rich import print
import pandas as pd
import datetime as dt
import numpy as np


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
            "campaign_start_date": "first",
            "campaign_end_date": "first",
            "mobile_app_install": "sum",
            "clicks": "sum",
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


@st.cache_data(ttl="1d", show_spinner="Getting LA")
def get_LA_totals(daterange, countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query(
        "@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list) and max_user_level >= 1"
    )
    return len(df_user_list)


@st.cache_data(ttl="1d", show_spinner=False)
def get_LR_totals(daterange, countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query(
        "@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list)"
    )
    return len(df_user_list)


@st.cache_data(ttl="1d", show_spinner="Calculating GC")
def get_GC_avg_by_date(daterange, countries_list):
    df_user_list = st.session_state.df_user_list
    df_user_list = df_user_list.query(
        "@daterange[0] <= first_open <= @daterange[1] and country.isin(@countries_list)"
    )
    df_user_list = df_user_list.fillna(0)
    return 0 if len(df_user_list) == 0 else np.average(df_user_list.gc)


def count_rows(df):
    return len(df)


@st.cache_data(ttl="1d", show_spinner=False)
def get_country_counts(daterange, countries_list, metric="LA"):
    df = st.session_state.df_user_list
    df = df.query("@daterange[0] <= first_open <= @daterange[1]")

    mask = df["country"].isin(countries_list)
    df = df[mask]

    if metric == "LA":
        country_counts = (
            df[df["max_user_level"] >= 1]
            .groupby("country")
            .size()
            .to_frame(name="LA")
            .reset_index()
            .sort_values(by="LA", ascending=False)
            .merge(
                df.groupby("country").size().to_frame(name="LR").reset_index(),
                on="country",
                how="left",
            )
            .fillna(0)
        )
    elif metric == "LR":
        country_counts = (
            df.groupby("country")
            .size()
            .to_frame(name="LR")
            .reset_index()
            .sort_values(by="LR", ascending=False)
            .merge(
                df[df["max_user_level"] >= 1]
                .groupby("country")
                .size()
                .to_frame(name="LA")
                .reset_index(),
                on="country",
                how="left",
            )
            .fillna(0)
        )
    else:
        # Calculate the average GC per country
        avg_gc_per_country = df.groupby("country")["gc"].mean().round(2)
        # Create a new DataFrame with the average GC per country
        country_counts = (
            pd.DataFrame(
                {"country": avg_gc_per_country.index, "GC": avg_gc_per_country.values}
            )
            .sort_values(by="GC", ascending=False)
            .fillna(0)
        )

    return country_counts
