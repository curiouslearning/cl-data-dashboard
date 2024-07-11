import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users

st.title("Curious Learning Dashboard")


settings.initialize()
settings.init_campaign_data()
settings.init_user_list()
ui.display_definitions_table(ui.level_definitions)
ui.colorize_multiselect_options()


selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)
if len(daterange) == 2:

    option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
    uic.lrc_scatter_chart(daterange,option)

    st.divider()
    st.subheader("Learners Reached Over Time")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        countries_list = users.get_country_list()
        countries_list = ui.multi_select_all(
            countries_list,
            title="Country Selection",
            key="LA_LR_Time",
            placement="middle",
        )
        languages = users.get_language_list()
        language = ui.single_selector(
            languages, placement="middle", title="Select a language", key="a-2"
        )
    with col2:
        app = ui.app_selector(placement="middle")
        option = st.radio(
            "Select a statistic", ("LR", "LA"), index=0, horizontal=True, key="a-1"
        )
        display_category = st.radio(
            "Display by", ("Country", "Language"), index=0, horizontal=True, key="a-3"
        )

    if (len(countries_list)) > 0 and (len(daterange) == 2):
        uic.LR_LA_line_chart_over_time(
            daterange, countries_list, app=app, language=language, option=option,display_category=display_category
        )

    st.divider()
    st.subheader("Total Spend per Country")
    uic.spend_by_country_map(daterange)

    st.divider()
    st.subheader("Campaign Timelines")
    uic.campaign_gantt_chart(daterange)
