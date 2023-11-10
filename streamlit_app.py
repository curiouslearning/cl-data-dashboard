import streamlit as st
import pandas as pd
import settings

import ui_components as ui

logger = settings.init_logging()
bq_client = settings.get_bq_client()


## UI ##
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

st.sidebar.markdown("***")
ui.calendar_selector()
