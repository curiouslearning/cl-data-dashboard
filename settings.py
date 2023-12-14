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
    pd.set_option('display.max_columns', 20); 
    logger = init_logging()
    bq_client = get_bq_client()
    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client

    
    #Get all of the data and store it
  #  df_events = events.get_play_event_data(bq_client)
    df_fb   = campaigns.get_fb_campaign_data(bq_client)
    df_goog = campaigns.get_google_campaign_data(bq_client)
    df_goog_conversions = campaigns.get_google_campaign_conversions(bq_client)
    df_goog = pd.concat( [df_goog,df_goog_conversions])
    df_all = pd.concat([df_fb, df_goog])


  #  if "df_events" not in st.session_state:
 #       st.session_state["df_events"] = df_events
    if "df_goog_conversions" not in st.session_state:
        st.session_state["df_goog_conversions"] = df_goog_conversions
    if "df_all" not in st.session_state:
        st.session_state["df_all"] = df_all
    if "logger" not in st.session_state:
        st.session_state["logger"] = logger
    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client

    