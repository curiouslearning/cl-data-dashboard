import google.cloud.logging
import streamlit as st
import logging
import os
from google.oauth2 import service_account
from google.cloud import bigquery
import campaigns
import play_data
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


@st.cache_resource
def get_logger():
    credentials = get_gcp_credentials()
    logging_client = google.cloud.logging.Client(credentials=credentials)
    logging_client.setup_logging(log_level=logging.DEBUG)
    logging_client.setup_logging()
    logger = logging.getLogger()

    if os.getenv("LOCAL_LOGGING", "False") == "True":
        # output logs to console - otherwise logs are only visible when running in GCP
        logger.addHandler(logging.StreamHandler())
    return logger


def initialize():
    pd.set_option("display.max_columns", 20)
    logger = get_logger()
    bq_client = get_bq_client()

    if "logger" not in st.session_state:
        st.session_state["logger"] = logger
    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client
    if "language" not in st.session_state:
        st.session_state.language = "All"
    logger.info("initialization complete")


def init_user_list():
    df_la, df_lr = users.get_users_list()
    if "df_la" not in st.session_state:
        st.session_state["df_la"] = df_la
    if "df_lr" not in st.session_state:
        st.session_state["df_lr"] = df_lr
    logger = get_logger()
    logger.info("user load complete")


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


def init_play_data():
    df_pd = play_data.get_play_installs()
    st.session_state["df_pd"] = df_pd
