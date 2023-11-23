import streamlit as st
import pandas as pd
import settings
import campaigns
from rich import print as rprint

import ui_components as ui

logger = settings.init_logging()
bq_client = settings.get_bq_client()



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
    df_fb = campaigns.get_fb_campaign_data_totals(bq_client,daterange)
    keys = [1,2,3,4,5]
    ui.paginated_dataframe(df_fb,keys)


if (platform == 'Google' or platform == 'Both'):
    st.header("Google Ads")
    df_goog = campaigns.get_google_campaign_data_totals(bq_client,daterange)
    keys = [6,7,8,9,10]
    ui.paginated_dataframe(df_goog,keys)

