import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as ui

st.title("Curious Learning Dashboard")
st.subheader("Acquisition Funnel")
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()
settings.init_play_data()

ui.funnel_chart()
