import streamlit as st
import pandas as pd
import settings
import campaigns
from rich import print as rprint

import ui_components as ui

logger = settings.init_logging()
bq_client = settings.get_bq_client()
key = 0


st.set_page_config(layout="wide") 

## UI ##
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

st.sidebar.markdown("***")
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

platform = ui.ads_platform_selector()

if (platform == 'Facebook' or platform == 'Both'):
    st.header("Facebook Ads")
    df = campaigns.get_fb_campaign_data_totals(bq_client,daterange)
    ui.paginated_dataframe(df)
    st.text( "rows = " + str(len(df)))

if (platform == 'Google' or platform == 'Both'):
    st.header("Google Ads")
    df = campaigns.get_google_campaign_data_totals(bq_client,daterange)
    ui.paginated_dataframe(df)
    st.text( "rows = " + str(len(df)))
