import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users

st.title("Curious Learning Dashboard")

ui.display_definitions_table()
settings.initialize()
settings.init_campaign_data()
settings.init_user_list()
ui.colorize_multiselect_options()
uic.lrc_scatter_chart()

st.divider()
st.subheader("Learners Reached Over Time")

col1, col2, col3 = st.columns(3, gap="large")
with col1:

    selected_date, option = ui.calendar_selector(placement="middle")
    daterange = ui.convert_date_to_range(selected_date, option)
    app = ui.app_selector(placement="middle")
    language = ui.language_selector(
        placement="middle"
    )  # puts selection in session state
with col2:
    countries_list = users.get_country_list()
    countries_list = ui.multi_select_all(
        countries_list,
        title="Country Selection",
        key="LA_LR_Time",
        placement="middle",
    )


option = st.radio("Select a statistic", ("LR", "LA"), index=0, horizontal=True, key="A")
if (len(countries_list)) > 0 and (len(daterange) == 2):
    uic.LR_LA_line_chart_over_time(
        daterange, countries_list, app=app, language=language, option=option
    )

st.divider()
st.subheader("Total Spend per Country")
uic.spend_by_country_map()

st.divider()
st.subheader("Campaign Timelines")
uic.campaign_gantt_chart()
