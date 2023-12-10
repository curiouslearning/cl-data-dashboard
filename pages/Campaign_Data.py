import streamlit as st
import settings
import metrics

import ui_components as ui

st.set_page_config(layout="wide") 

## UI ##
st.title("Curious Learning Dashboard")
settings.initialize()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

platform = ui.ads_platform_selector()

if (platform == 'Facebook' or platform == 'Both'):
    st.header("Facebook Ads")
    df = metrics.get_campaign_data_totals(daterange,'Facebook')
    if (len(df) > 0):
        keys = [1,2,3,4,5]
        ui.paginated_dataframe(df,keys)
    else:
        st.text("No data for selected period")


if (platform == 'Google' or platform == 'Both'):
    st.header("Google Ads")
    df = metrics.get_campaign_data_totals(daterange,'Google')
    if (len(df) > 0):
        keys = [6,7,8,9,10]
        df.sort_values(by="button_clicks")

        ui.paginated_dataframe(df,keys)
    else:
        st.text("No data for selected period")

