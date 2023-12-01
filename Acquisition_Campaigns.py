import streamlit as st
import pandas as pd
import settings
import campaigns
import datetime as dt
from rich import print as rprint

import ui_components as ui

st.set_page_config(layout="wide") 



## UI ##
st.title("Curious Learning Dashboard")


    

ui.display_definitions_table()

st.sidebar.markdown("***")
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

