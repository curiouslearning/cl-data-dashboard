import streamlit as st
import pandas as pd
import settings
from rich import print as rprint
import metrics
from millify import prettify

import ui_components as ui

st.title("Curious Learning Dashboard")

ui.display_definitions_table()
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()
settings.clear_selector_session_state()
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    st.subheader("Campaign Timelines and Performance")
    ui.campaign_gantt_chart(daterange)

    st.subheader("Top 10 Campaigns")
    ui.top_campaigns_by_downloads_barchart(10)
