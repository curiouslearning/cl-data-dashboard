import streamlit as st

import ui_components as ui

st.title("Curious Learning Dashboard")

st.subheader("First Open by Country")

ui.display_definitions_table()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

ui.actions_by_country_map(daterange)
