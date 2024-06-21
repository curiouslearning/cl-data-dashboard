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

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]


def get_gcp_credentials():
    # first get credentials to secret manager
    client = secretmanager.SecretManagerServiceClient()

    # get the secret that holds the service account key
    name = "projects/405806232197/secrets/service_account_json/versions/latest"
    response = client.access_secret_version(name=name)
    key = response.payload.data.decode("UTF-8")

    # use the key to get service account credentials
    service_account_info = json.loads(key)
    # Create BigQuery API client.
    gcp_credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ],
    )

    bq_client = bigquery.Client(
        credentials=gcp_credentials, project="dataexploration-193817"
    )
    return bq_client


def initialize():
    pd.options.mode.copy_on_write = True
    pd.set_option("display.max_columns", 20)

    bq_client = get_gcp_credentials()

    if "bq_client" not in st.session_state:
        st.session_state["bq_client"] = bq_client


def init_user_list():
    df_user_list, df_first_open = users.get_users_list()
    if "df_user_list" not in st.session_state:
        st.session_state["df_user_list"] = df_user_list
    if "df_first_open" not in st.session_state:
        st.session_state["df_first_open"] = df_first_open


# Get the campaign data from BigQuery, roll it up per campaign
def init_campaign_data():
    df_fb_all = campaigns.get_fb_campaign_data()

    df_goog_all = campaigns.get_google_campaign_data()
    df_campaigns_all = pd.concat([df_goog_all, df_fb_all])
    df_campaigns_all = campaigns.add_country_and_language(df_campaigns_all)

    df_campaigns = campaigns.rollup_campaign_data(df_campaigns_all)

    df_campaigns = campaigns.add_country_and_language(df_campaigns)

    df_campaigns = campaigns.add_google_button_clicks(df_campaigns, default_daterange)

    if "df_campaigns" not in st.session_state:
        st.session_state["df_campaigns"] = df_campaigns

    if "df_campaigns_all" not in st.session_state:
        st.session_state["df_campaigns_all"] = df_campaigns_all


def init_cr_app_version_list():
    cr_app_versions_list = users.get_app_version_list()
    if "cr_app_versions_list" not in st.session_state:
        st.session_state.cr_app_versions_list = cr_app_versions_list
