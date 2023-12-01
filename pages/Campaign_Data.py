import streamlit as st
import pandas as pd
import settings
import campaigns
import rich 
import datetime as dt

import ui_components as ui

st.set_page_config(layout="wide") 

## UI ##
st.title("Curious Learning Dashboard")
settings.initialize()

st.sidebar.markdown("***")
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

platform = ui.ads_platform_selector()



if (platform == 'Facebook' or platform == 'Both'):
    st.header("Facebook Ads")
    df_fb = st.session_state.df_fb
    if (len(df_fb) > 0):
        keys = [1,2,3,4,5]
        ui.paginated_dataframe(df_fb,keys)
    else:
        st.text("No data for selected period")


if (platform == 'Google' or platform == 'Both'):
    st.header("Google Ads")
    df_goog = st.session_state.df_goog
    if (len(df_goog) > 0):
        keys = [6,7,8,9,10]
        ui.paginated_dataframe(df_goog,keys)
    else:
        st.text("No data for selected period")

