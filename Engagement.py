import streamlit as st
import settings
from rich import print
import metrics
from millify import prettify
import ui_components as ui
import users
import plotly.graph_objects as go
import plotly.express as px


st.set_page_config(layout="wide")
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

settings.initialize()
settings.init_user_list()


selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

# language = ui.language_selector()
language = "All"

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(countries_list, title="Country Selection")

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")
    st.subheader("General Engagement")
    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)

    total = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", language=language
    )
    col1.metric(label="Learners Reached", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(
        daterange, countries_list, "LA", language=language
    )
    col2.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics.get_GC_avg_by_date(daterange, countries_list, language=language)
    col3.metric(label="Game Completion Average", value=f"{total:.2f}%")

    st.divider()

    st.subheader("Engagement across the world")
    ui.stats_by_country_map(daterange, countries_list, language)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        ui.top_LR_LC_bar_chart(daterange, countries_list, language)
    with c2:
        st.markdown("***")
        st.markdown("***")
        ui.top_gc_bar_chart(daterange, countries_list, language)

    st.divider()
    st.subheader("Engagement over time")
    ui.LR_LA_line_chart_over_time(daterange, countries_list)
