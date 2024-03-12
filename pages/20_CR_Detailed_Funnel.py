import streamlit as st
import settings
import ui_components as uic


st.title("Curious Learning Dashboard")
settings.initialize()
settings.init_user_list()

uic.cr_funnel_chart_details()
