import google.cloud.logging
import streamlit as st
import logging
import os
from google.oauth2 import service_account
from google.cloud import bigquery

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

