import streamlit as st
from settings import initialize
from metrics import get_cohort_totals_by_metric,get_cohort_GPP_avg,get_filtered_cohort,get_cohort_GC_avg
from settings import initialize
from users import ensure_user_data_initialized
from millify import prettify
import ui_widgets as ui
from users import get_language_list,get_country_list
from ui_components import levels_reached_chart,stats_by_country_map,top_stats_bar_chart

st.set_page_config(layout="wide")

ui.display_definitions_table("Definitions",ui.level_definitions)
ui.display_definitions_table("Data Notes",ui.data_notes)

initialize()
ensure_user_data_initialized()

with st.sidebar:
    languages = get_language_list()
    language = ui.single_selector(
        languages, title="Select a language", key="e-1"
    )

    countries_list = get_country_list()
    countries_list = ui.multi_select_all(
        countries_list, title="Country Selection", key="e-2"
    )

    selected_date, option = ui.calendar_selector()
    daterange = ui.convert_date_to_range(selected_date, option)

    apps = ui.get_apps()
    app = ui.single_selector(apps, title="Select an App", key="sf-10",include_All=False)

# In the case of datepicker, don't do anything until both start and end dates are picked
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(date_start + " to " + date_end)

    col1, col2, col3 = st.columns(3)
    
    user_cohort_df, user_cohort_df_LR = get_filtered_cohort(app, daterange, language, countries_list)
    if (app == ["CR"] or app == "CR"):
        LR_df = user_cohort_df_LR
    else:
        LR_df = user_cohort_df
    
    LR = get_cohort_totals_by_metric(LR_df,stat="LR")
    col1.metric(label="Learners Reached", value=prettify(int(LR)))

    LA = get_cohort_totals_by_metric(user_cohort_df,stat="LA")
    col2.metric(label="Learners Acquired", value=prettify(int(LA)))   
     
    RA = get_cohort_totals_by_metric(user_cohort_df,stat="RA")
    col3.metric(label="Readers Acquired", value=prettify(int(RA)))
    
    GC = get_cohort_totals_by_metric(user_cohort_df,stat="GC")
    col1.metric(label="Games Completed", value=prettify(int(GC)))

    GPP = get_cohort_GPP_avg(user_cohort_df)
    col2.metric(label="Game Progress Percent", value=f"{GPP:.2f}%")

    GC_AVG = get_cohort_GC_avg(user_cohort_df)
    col3.metric(label="Game Completion Avg", value=f"{GC_AVG:.2f}%")

    st.divider()
    st.subheader("Levels reached per language")
    levels_reached_chart(apps)

    csv = ui.convert_for_download(user_cohort_df)
    st.download_button(label="Download CSV",data=csv,file_name="user_cohort_df.csv",key="e-10",icon=":material/download:",mime="text/csv")


    st.divider()
    st.subheader("Engagement across the world")

    option = ui.stats_radio_selector()  # e.g., "LR", "LA", "RA", "GC", etc.

    # 2️⃣ Determine which dataframe to use for the base cohort
    # For CR, LR data comes from the separate cohort_df_LR
    if app == ["CR"] or app == "CR":
        df_main = user_cohort_df_LR if option == "LR" else user_cohort_df
    else:
        df_main = user_cohort_df

    # 3️⃣ Draw the map (and return the dataframe for download)
    df_download = stats_by_country_map(
        user_cohort_df=df_main,
        user_cohort_df_LR=user_cohort_df_LR,
        app=app,
        option=option,
        min_funnel=True,
        sort_by="Total",  # or "Percent" if you prefer
    )

    st.divider()
    st.subheader("Top 10's")

    c1, c2, = st.columns(2)
    with c1:
        option = st.radio("Select a statistic", ("LR", "LA", "RA", "GC" ,"GPP", "GCA"), index=0, horizontal=True,key="e-3")
    with c2:
        display_category = st.radio(
            "Display by", ("Country", "Language"), index=0, horizontal=True, key="e-4"
        )
    
    if option == "LR" and (app == ["CR"] or app == "CR"):
        user_cohort_df = LR_df
    df_download = top_stats_bar_chart(user_cohort_df=user_cohort_df, option=option,display_category=display_category,app=app )
    
    csv = ui.convert_for_download(df_download)
    st.download_button(label="Download CSV",data=csv,file_name="top_LR_LC_bar_chart.csv",key="e-12",icon=":material/download:",mime="text/csv")
