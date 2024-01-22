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
countries_list = users.get_country_list()
countries_list = ui.multi_select_all(countries_list, title="Country Selection")

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)

    total = metrics.get_LR_totals(daterange, countries_list)
    col1.metric(label="Learners Reached", value=prettify(int(total)))

    total = metrics.get_LA_totals(daterange, countries_list)
    col2.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics.get_GC_avg_by_date(daterange, countries_list)
    col3.metric(label="Game Completion Average", value=f"{total:.2f}%")

    st.divider()
    option = st.radio("Select a statistic", ("LR", "LA"), index=0, horizontal=True)
    df = metrics.get_country_counts(daterange, countries_list, str(option)).head(10)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 Countries by " + str(option))
        fig = go.Figure(
            data=[
                go.Bar(name="LR", x=df["country"], y=df["LR"]),
                go.Bar(name="LA", x=df["country"], y=df["LA"]),
            ]
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Top 10 Countries by GC %")
        df = metrics.get_country_counts(daterange, countries_list, "GC").head(10)
        fig = px.bar(df, x="country", y="GC", color="GC")

        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    ui.stats_by_country_map(daterange, countries_list)
