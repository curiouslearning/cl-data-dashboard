import streamlit as st
import pandas as pd
import settings
from rich import print as rprint
import metrics
from millify import prettify




import ui_components as ui

st.set_page_config(layout="wide") 
settings.initialize()



## UI ##
st.title("Curious Learning Dashboard")


ui.display_definitions_table()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

date_start = daterange[0].strftime("%Y-%m-%d")
date_end= daterange[1].strftime("%Y-%m-%d")

st.markdown("**Selected Range:**")
st.text(date_start + " to " + date_end)

col1, col2, col3 = st.columns(3)

total = metrics.get_first_open_totals(daterange)
col1.metric(label="FIRST OPEN", value=prettify(int(total)))

cost_per_download = metrics.get_ave_cost_per_action(daterange)
col2.metric(label="AVE COST PER INSTALL", value='${:,.2f}'.format(cost_per_download))

button_clicks = metrics.get_google_conversions(daterange)
col3.metric(label="Google Button Clicks", value=prettify(int(button_clicks)))

st.subheader("Top 10 Campaigns")
ui.top_campaigns_by_downloads_barchart(10)

