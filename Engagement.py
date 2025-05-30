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
st.subheader("Page Purpose: Explore the user statistics")

ui.display_definitions_table("Definitions",ui.level_definitions)
ui.display_definitions_table("Data Notes",ui.data_notes)
settings.initialize()
settings.init_user_list()

ui.colorize_multiselect_options()

selected_date, option = ui.calendar_selector()
daterange = ui.convert_date_to_range(selected_date, option)

languages = users.get_language_list()
language = ui.single_selector(
    languages, title="Select a language", placement="side", key="e-1"
)

countries_list = users.get_country_list()
countries_list = ui.multi_select_all(
    countries_list, title="Country Selection", key="e-2"
)

app = ui.app_selector()
# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")
    st.subheader("General Engagement")
    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)

    total = metrics.get_totals_by_metric(
        daterange, countries_list, stat="LR", app=app, language=language
    )
    col1.metric(label="Learners Reached", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(
        daterange, countries_list, "LA", app=app, language=language
    )
    col2.metric(label="Learners Acquired", value=prettify(int(total)))

    total = metrics.get_totals_by_metric(
        daterange, countries_list, "RA", app=app, language=language
    )
    col3.metric(label="Readers Acquired", value=prettify(int(total)))


    total = metrics.get_totals_by_metric(
        daterange, countries_list, "GC", app=app, language=language
    )
    col1.metric(label="Games Completed", value=prettify(int(total)))

    total = metrics.get_GPP_avg(daterange, countries_list, app=app, language=language)
    col2.metric(label="Game Progress Percent", value=f"{total:.2f}%")

    total = metrics.get_GC_avg(daterange, countries_list, app=app, language=language)
    col3.metric(label="Game Completion Avg", value=f"{total:.2f}%")

    st.divider()
    st.subheader("Levels reached per language")
    
    df_download = uic.levels_line_chart(daterange, countries_list, app=app, language=language)
    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download CSV",data=csv,file_name="levels.csv",key="e-10",icon=":material/download:",mime="text/csv")


    st.divider()
    st.subheader("Engagement across the world")

    option = ui.stats_radio_selector()
    df_download = uic.stats_by_country_map(
        daterange, countries_list, app=app, language=language, option=option
    )
    
    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download CSV",data=csv,file_name="stats_per_country.csv",key="e-11",icon=":material/download:",mime="text/csv")

    st.divider()
    st.subheader("Top 10's")

    c1, c2, c3,c4 = st.columns(4)
    with c1:
        option = st.radio("Select a statistic", ("LR", "LA", "RA"), index=0, horizontal=True,key="e-3")
    with c2:
        display_category = st.radio(
            "Display by", ("Country", "Language"), index=0, horizontal=True, key="e-4"
        )
    
    df_download = uic.top_LR_LC_bar_chart(
        daterange, countries_list, option, app=app, language=language,display_category=display_category)
    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download CSV",data=csv,file_name="top_LR_LC_bar_chart.csv",key="e-12",icon=":material/download:",mime="text/csv")

    c1, c2 = st.columns(2)
    with c1:
        df_download = uic.top_gpp_bar_chart(daterange, countries_list, app=app, language=language,display_category=display_category)
        csv = ui.convert_for_download(df_download)
        st.download_button(label="Download CSV",data=csv,file_name="top_gpp_bar_chart.csv",key="e-13",icon=":material/download:",mime="text/csv")

    with c2:
        df_download =  uic.top_gca_bar_chart(daterange, countries_list, app=app, language=language,display_category=display_category)
        csv = ui.convert_for_download(df_download)
        st.download_button(label="Download CSV",data=csv,file_name="top_gca_bar_chart.csv",key="e-14",icon=":material/download:",mime="text/csv")
