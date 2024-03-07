import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui


st.title("Curious Learning Dashboard")
st.subheader("Acquisition Funnel")
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()

ui.app_selector()

uic.campaign_funnel_chart()
uic.engagement_funnel_chart()
