import streamlit as st
import pandas as pd
import settings
from rich import print as rprint
import metrics
from millify import prettify

import ui_components as ui

st.set_page_config(layout="wide") 
settings.initialize()


st.title("Curious Learning Dashboard")


ui.display_definitions_table()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date,option)

# In the case of datepicker, don't do anything until both start and end dates are picked
if (len(daterange) == 2):
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end= daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3, col4 = st.columns(4)

    total = metrics.get_LR_totals(daterange)
    col1.metric(label="LEARNERS REACHED", value=prettify(int(total)))

 #   total = metrics.get_download_totals(daterange)
 #   col2.metric(label="FACEBOOK DOWNLOADS", value=prettify(int(total)))

    cost_per_download = metrics.get_ave_cost_per_action(daterange)
    col3.metric(label="AVE COST PER INSTALL", value='${:,.2f}'.format(cost_per_download))

  #  button_clicks = metrics.get_google_conversions(daterange)
 #   col4.metric(label="GOOGLE BUTTON CLICKS", value=prettify(int(button_clicks)))

    st.subheader("Campaign Timelines and Performance")
    ui.campaign_gantt_chart(daterange)

    st.subheader("Top 10 Campaigns")
    ui.top_campaigns_by_downloads_barchart(10)



