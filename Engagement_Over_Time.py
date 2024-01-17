import streamlit as st
import settings
from rich import print
import metrics
from millify import prettify
import ui_components as ui
import users

st.title("Curious Learning Dashboard")

ui.display_definitions_table()

settings.initialize()
settings.init_user_list()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)
countries_list = users.get_country_list()
countries_list = ui.multi_select_all(countries_list)
# In the case of datepicker, don't do anything until both start and end dates are picked
if (len(daterange) == 2):
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3, col4 = st.columns(4)

    total = metrics.get_LR_totals(daterange,countries_list)
    col1.metric(label="Learners Reached", value=prettify(int(total)))
    
    total = metrics.get_LA_totals(daterange,countries_list)
    col2.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics. get_GC_avg_by_date(daterange,countries_list)
    col3.metric(label="Game Completion Average", value=f"{total:.2f}%")


ui.LA_by_country_map(daterange,countries_list)
