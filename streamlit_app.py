import streamlit as st
import pandas as pd
import settings
import campaigns
from rich import print as rprint

import ui_components as ui

logger = settings.init_logging()
bq_client = settings.get_bq_client()


## UI ##
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

st.sidebar.markdown("***")
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

st.header("Facebook Ads")
df = campaigns.get_fb_campaign_data_totals(bq_client,daterange)
#st.table(df)
st.text( "rows = " + str(len(df)))

st.header("Google Ads")
df = campaigns.get_google_campaign_data_totals(bq_client,daterange)
#st.table(df)
st.text( "rows = " + str(len(df)))
