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
settings.init_campaign_data()
settings.init_user_list()

ui.colorize_multiselect_options()
app = ui.app_selector()
language = ui.language_selector()  # puts selection in session state
countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="funnel_compare_key"
)

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)
if len(daterange) == 2:
    st.subheader("Campaign Funnel")

    df_campaigns = st.session_state.df_campaigns
    impressions = df_campaigns["impressions"].sum()
    clicks = df_campaigns["clicks"].sum()

    funnel_data = {
        "Title": [
            "Impressions",
            "Clicks",
        ],
        "Count": [impressions, clicks],
    }

    fig = uic.create_engagement_figure(funnel_data)
    fig.update_layout(
        height=200,
    )
    st.plotly_chart(fig, use_container_width=True)

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
    GC = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app=app, language=language
    )

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }
    fig = uic.create_engagement_figure(funnel_data)
    st.plotly_chart(fig, use_container_width=True)
