import streamlit as st
import settings
from rich import print as rprint
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import metrics
import users


st.title("Curious Learning Dashboard")

settings.initialize()
settings.init_user_list()

ui.display_definitions_table("Definitions",ui.level_definitions)
ui.display_definitions_table("Data Notes",ui.data_notes)
ui.colorize_multiselect_options()
app = ui.app_selector()

languages = users.get_language_list()
language = ui.single_selector(
    languages, placement="side", title="Select a language", key="af-1"
)

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="af-2"
)

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)
if len(daterange) == 2:


    start = daterange[0].strftime("%m-%d-%Y")
    end = daterange[1].strftime("%m-%d-%Y")
    st.subheader("Acquisition Funnel: " + start + " - " + end)

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app=app, language=language
    )
    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app=app, language=language
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app=app, language=language
    )
    RA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="RA", app=app, language=language
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app=app, language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Readers Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, RA,GC],
    }
    fig = uic.create_engagement_figure(funnel_data)
    st.plotly_chart(fig, use_container_width=True)
