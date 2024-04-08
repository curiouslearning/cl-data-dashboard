import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui

st.title("Curious Learning Dashboard")

ui.display_definitions_table()
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()

uic.lrc_scatter_chart()
st.divider()
st.subheader("Campaign Timelines")
uic.campaign_gantt_chart()
st.divider()
st.subheader("Total Spend per Country")
uic.spend_by_country_map()
