import streamlit as st
import settings
from rich import print
import metrics
from millify import prettify
import ui_components as uic
import ui_widgets as ui
import users

st.set_page_config(layout="wide")
st.title("Curious Learning Dashboard")

ui.display_definitions_table()

settings.initialize()
settings.init_user_list()
selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)
print(str(type(daterange)))
print(daterange)

ui.language_selector()  # puts selection in session state

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="engagement_page"
)

ui.app_selector()
# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")
    st.subheader("General Engagement")
    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)

    total = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    col1.metric(label="Learners Reached", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    col2.metric(label="Puzzle Completed", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(daterange, countries_list, "LA")
    col3.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(daterange, countries_list, "GC")
    col1.metric(label="Games Completed", value=prettify(int(total)))

    total = metrics.get_GPP_avg(daterange, countries_list)
    col2.metric(label="Game Progress Percent", value=f"{total:.2f}%")

    total = metrics.get_GC_avg(daterange, countries_list)
    col3.metric(label="Game Completion Avg", value=f"{total:.2f}%")

    st.divider()

    st.subheader("Engagement across the world")
    uic.stats_by_country_map(daterange, countries_list)
    st.divider()
    option = st.radio("Select a statistic", ("LR", "LA"), index=0, horizontal=True)
    uic.top_LR_LC_bar_chart(daterange, countries_list, option)
    c1, c2 = st.columns(2)
    with c1:
        uic.top_gpc_bar_chart(daterange, countries_list)
    with c2:
        uic.top_gca_bar_chart(daterange, countries_list)

    st.divider()
    st.subheader("Engagement over time")
    option = st.radio(
        "Select a statistic", ("LR", "LA"), index=0, horizontal=True, key="A"
    )

    uic.LR_LA_line_chart_over_time(daterange, countries_list, option)
