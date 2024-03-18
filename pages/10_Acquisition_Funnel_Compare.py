import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users

st.title("Curious Learning Dashboard")
st.subheader("Acquisition Funnel Comparison")
settings.initialize()
settings.init_user_list()

uic.engagement_funnel_chart_compare()
uic.cr_funnel_chart_details()
