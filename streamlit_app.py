import streamlit as st
import pandas as pd
import settings
import campaigns

import ui_components as ui

logger = settings.init_logging()
bq_client = settings.get_bq_client()


## UI ##
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

st.sidebar.markdown("***")
selected_date = ui.calendar_selector()
print (type(selected_date))
st.text(selected_date)

df = campaigns.get_campaign_data(bq_client)
st.text(df)
