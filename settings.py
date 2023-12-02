import google.cloud.logging
import streamlit as st
import logging
import os
import datetime as dt
from google.oauth2 import service_account
from google.cloud import bigquery
import campaigns
import rich
import pandas as pd

st.cache_resource
def get_bq_client():
    credentials = get_gcp_credentials()
    bq_client = bigquery.Client(credentials=credentials)
    return bq_client

st.cache_resource
def get_gcp_credentials():
    # Create BigQuery API client.
    gcp_credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"])
    return gcp_credentials

st.cache_resource
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

def initialize():
    logger = init_logging()
    bq_client = get_bq_client()
    
    #Get all of the data and store it
    default_date_range = [dt.datetime(2020,1,1),dt.date.today()]
    df_fb   = campaigns.get_fb_campaign_data(bq_client)
    df_goog = campaigns.get_google_campaign_data(bq_client)
    df_all = pd.concat([df_fb, df_goog])


    if "df_goog" not in st.session_state:
        st.session_state["df_goog"] = df_goog
    if "df_fb" not in st.session_state:
        st.session_state["df_fb"] = df_fb    
    if "df_all" not in st.session_state:
        st.session_state["df_all"] = df_all
    if "logger" not in st.session_state:
        st.session_state["logger"] = logger
    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client

    