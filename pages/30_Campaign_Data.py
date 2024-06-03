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
settings.init_user_list()

platform = ui.ads_platform_selector()
col1, col2 = st.columns(2)

selected_date, option = ui.calendar_selector(placement="side", key="fh-3", index=0)
daterange = ui.convert_date_to_range(selected_date, option)

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) > 1:
    df_campaigns = metrics.get_campaigns_by_date(daterange)

    # Drop the campaigns that don't meet the naming convention
    condition = (df_campaigns["app_language"].isna()) | (df_campaigns["country"].isna())
    df_campaigns = df_campaigns[~condition]

    col = df_campaigns.pop("country")
    df_campaigns.insert(2, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    col = df_campaigns.pop("app_language")
    df_campaigns.insert(3, col.name, col)
    df_campaigns.reset_index(drop=True, inplace=True)

    st.header("Marketing Performance Table")
    df = metrics.build_campaign_table(df_campaigns, daterange)
    keys = [12, 13, 14, 15, 16]
    ui.paginated_dataframe(df, keys, sort_col="country")

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
