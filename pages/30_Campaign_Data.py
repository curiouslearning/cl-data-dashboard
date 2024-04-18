import streamlit as st
import settings
import metrics
from millify import prettify

import ui_widgets as ui

st.set_page_config(layout="wide")

## UI ##
st.title("Curious Learning Dashboard")
settings.initialize()
settings.init_campaign_data()

platform = ui.ads_platform_selector()
col1, col2 = st.columns(2)

# In the case of datepicker, don't do anything until both start and end dates are picked


total_fb, total_goog = metrics.get_download_totals()

col1.metric(label="INSTALLS FROM FACEBOOK", value=prettify(int(total_fb)))
col2.metric(label="GOOGLE CONVERSIONS", value=prettify(int(total_goog)))

if "df_campaigns" in st.session_state:
    df_campaigns = st.session_state.df_campaigns
    if platform == "Facebook" or platform == "Both":
        st.header("Facebook Ads")

        dff = df_campaigns.query("source == 'Facebook'")

        if len(dff) > 0:
            keys = [2, 3, 4, 5, 6]
            ui.paginated_dataframe(dff, keys, sort_col="campaign_name")
        else:
            st.text("No data for selected period")

    if platform == "Google" or platform == "Both":
        st.header("Google Ads")
        dfg = df_campaigns.query("source == 'Google'")

        if len(dfg) > 0:
            keys = [7, 8, 9, 10, 11]
            dfg.sort_values(by="button_clicks")
            ui.paginated_dataframe(dfg, keys, sort_col="campaign_name")
        else:
            st.text("No data for selected period")
