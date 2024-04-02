import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import campaigns
from rich import print
import pandas as pd
import users


def get_bq_client():
    credentials = get_gcp_credentials()
    bq_client = bigquery.Client(credentials=credentials)
    return bq_client


def get_gcp_credentials():
    # Create BigQuery API client.
    gcp_credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ],
    )
    return gcp_credentials


def initialize():
    pd.options.mode.copy_on_write = True
    pd.set_option("display.max_columns", 20)
    bq_client = get_bq_client()

    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client


def init_user_list():
    df_user_list, df_first_open = users.get_users_list()
    if "df_user_list" not in st.session_state:
        st.session_state["df_user_list"] = df_user_list
    if "df_first_open" not in st.session_state:
        st.session_state["df_first_open"] = df_first_open


def init_campaign_data():
    df_fb = campaigns.get_fb_campaign_data()
    df_goog = campaigns.get_google_campaign_data()
    df_goog_conversions = campaigns.get_google_campaign_conversions()
    df_goog = pd.concat([df_goog, df_goog_conversions])

    df_fb = campaigns.rollup_campaign_data(df_fb)
    df_goog = campaigns.rollup_campaign_data(df_goog)
    df_campaigns = pd.concat([df_fb, df_goog])

    df_campaigns = campaigns.add_campaign_country(df_campaigns)

    df_campaigns.reset_index(drop=True, inplace=True)
    df_campaigns.set_index("campaign_name")

    if "df_campaigns" not in st.session_state:
        st.session_state["df_campaigns"] = df_campaigns


def init_cr_app_version_list():
    cr_app_versions_list = users.get_app_version_list()
    if "cr_app_versions_list" not in st.session_state:
        st.session_state.cr_app_versions_list = cr_app_versions_list
