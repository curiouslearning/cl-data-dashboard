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
from users import ensure_user_data_initialized
ensure_user_data_initialized()

ui.display_definitions_table("Definitions",ui.level_definitions)
ui.display_definitions_table("Data Notes",ui.data_notes)
ui.colorize_multiselect_options()


languages = users.get_language_list()
language = ui.single_selector(
    languages, title="Select a language", key="af-1"
)

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="af-2"
)

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

app = ui.app_selector()

if len(daterange) == 2 and len(language) > 0:
    user_cohort_list = []
    user_cohort_list = metrics.get_user_cohort_list(daterange=daterange,languages=language,countries_list=countries_list,app=app)
 
    start = daterange[0].strftime("%m-%d-%Y")
    end = daterange[1].strftime("%m-%d-%Y")
    st.subheader("Acquisition Funnel: " + start + " - " + end)

    LR = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app=app, language=language,user_list=user_cohort_list
    )
    PC = metrics.get_totals_by_metric(
        daterange, countries_list, "PC", app=app, language=language,user_list=user_cohort_list
    )
    LA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LA", app=app, language=language,user_list=user_cohort_list
    )
    RA = metrics.get_totals_by_metric(
        daterange, countries_list, stat="RA", app=app, language=language,user_list=user_cohort_list
    )
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app=app, language=language,user_list=user_cohort_list
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
