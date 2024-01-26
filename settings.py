import google.cloud.logging
import streamlit as st
import logging
import os
import datetime as dt
from google.oauth2 import service_account
from google.cloud import bigquery
import campaigns
from rich import print
import pandas as pd
import users


@st.cache_resource
def get_bq_client():
    credentials = get_gcp_credentials()
    bq_client = bigquery.Client(credentials=credentials)
    return bq_client


@st.cache_resource
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


@st.cache_resource
def init_logging():
    credentials = get_gcp_credentials()
    logging_client = google.cloud.logging.Client(credentials=credentials)
    logging_client.setup_logging(log_level=logging.DEBUG)
    logging_client.setup_logging()
    logger = logging.getLogger()

    if os.getenv("LOCAL_LOGGING", "False") == "True":
        # output logs to console - otherwise logs are only visible when running in GCP
        logger.addHandler(logging.StreamHandler())
    return logger


@st.cache_data(show_spinner=False, ttl="1d")
def initialize():
    pd.set_option("display.max_columns", 20)
    logger = init_logging()
    bq_client = get_bq_client()

    if "logger" not in st.session_state:
        st.session_state["logger"] = logger
    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client
    if "language" not in st.session_state:
        st.session_state.language = "All"


@st.cache_data(show_spinner=False, ttl="1d")
def init_user_list():
    df_user_list = users.get_users_list()
    if "df_user_list" not in st.session_state:
        st.session_state["df_user_list"] = df_user_list


@st.cache_data(show_spinner=False, ttl="1d")
def init_campaign_data():
    df_fb = campaigns.get_fb_campaign_data()
    df_goog = campaigns.get_google_campaign_data()
    df_goog_conversions = campaigns.get_google_campaign_conversions()
    df_goog = pd.concat([df_goog, df_goog_conversions])
    df_all = pd.concat([df_fb, df_goog])
    if "df_goog_conversions" not in st.session_state:
        st.session_state["df_goog_conversions"] = df_goog_conversions
    if "df_all" not in st.session_state:
        st.session_state["df_all"] = df_all


# Ensure that the selector sessions are reset when moving from page to page and back
def clear_selector_session_state():
    if "max_selections" in st.session_state:
        del st.session_state["max_selections"]
    if "selected_options" in st.session_state:
        del st.session_state["selected_options"]
