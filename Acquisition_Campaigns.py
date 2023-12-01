import streamlit as st
import pandas as pd
import settings
from rich import print as rprint
import metrics
from millify import prettify


import ui_components as ui

st.set_page_config(layout="wide") 
settings.initialize()



## UI ##
st.title("Curious Learning Dashboard")


    

ui.display_definitions_table()

st.sidebar.markdown("***")
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

col1, col2, col3 = st.columns(3)
total = metrics.get_download_totals(daterange)
col1.metric(label="TOTAL INSTALLS", value=prettify(int(total)), delta="0")


