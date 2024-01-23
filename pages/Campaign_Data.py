import streamlit as st
import settings
import metrics
from millify import prettify

import ui_components as ui

st.set_page_config(layout="wide")

## UI ##
st.title("Curious Learning Dashboard")
settings.initialize()
settings.init_campaign_data()
settings.clear_selector_session_state()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

platform = ui.ads_platform_selector()
col1, col2 = st.columns(2)

dff = metrics.get_campaign_data_totals(daterange, "Facebook")
dfg = metrics.get_campaign_data_totals(daterange, "Google")
total = metrics.get_download_totals(daterange)
button_clicks = metrics.get_google_conversions(daterange)

col1.metric(label="INSTALLS FROM FACEBOOK", value=prettify(int(total)))
col2.metric(label="GOOGLE CONVERSIONS", value=prettify(int(button_clicks)))

if platform == "Facebook" or platform == "Both":
    st.header("Facebook Ads")

    if len(dff) > 0:
        keys = [1, 2, 3, 4, 5]
        ui.paginated_dataframe(dff, keys)
    else:
        st.text("No data for selected period")


if platform == "Google" or platform == "Both":
    st.header("Google Ads")

    if len(dfg) > 0:
        keys = [6, 7, 8, 9, 10]
        dfg.sort_values(by="button_clicks")
        ui.paginated_dataframe(dfg, keys)
    else:
        st.text("No data for selected period")
