import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import campaigns
from rich import print
import pandas as pd
import users
import datetime as dt
from google.cloud import secretmanager
import json
import asyncio
from pyinstrument import Profiler
from pyinstrument.renderers.console import ConsoleRenderer
import logging

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]


@st.cache_resource(ttl="1d")
def get_logger(name="dashboard_logger"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Console handler or file handler
        handler = logging.StreamHandler()  # or logging.FileHandler("logs/app.log")
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False  # Prevent double logging
    return logger

@st.cache_resource(ttl="1d")
def get_gcp_credentials():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/405806232197/secrets/service_account_json/versions/latest"
    response = client.access_secret_version(name=name)
    key = response.payload.data.decode("UTF-8")

    service_account_info = json.loads(key)
    gcp_credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    bq_client = bigquery.Client(
        credentials=gcp_credentials, project="dataexploration-193817"
    )

    return gcp_credentials, bq_client



def initialize():  
    pd.options.mode.copy_on_write = True
    pd.set_option("display.max_columns", 20)            



# Get the campaign data from BigQuery, roll it up per campaign
def init_campaign_data():
# Call the combined asynchronous campaign data function
    df_goog_all, df_fb_all = cache_marketing_data()

    #Get all campaign data by segment_date
    df_campaigns_all = pd.concat([df_goog_all, df_fb_all])
    df_campaigns_all = campaigns.add_country_and_language(df_campaigns_all)
    df_campaigns_all = df_campaigns_all.reset_index(drop=True)

    if "df_campaigns_all" not in st.session_state:
        st.session_state["df_campaigns_all"] = df_campaigns_all

@st.cache_data(ttl="1d", show_spinner="Gathering Marketing Data")
def cache_marketing_data():
    # Execute the async function and return its result synchronously
    return asyncio.run(campaigns.get_campaign_data())



