import streamlit as st
from rich import print as rprint
from  ui_components import create_funnels_by_cohort
import ui_widgets as ui
import metrics
from users import ensure_user_data_initialized,get_language_list,get_country_list
from settings import initialize,init_cr_app_version_list

initialize()
init_cr_app_version_list()
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes",ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()

distinct_apps = ui.get_apps()

with st.sidebar:

    language = ui.single_selector(languages, title="Select a language", key="s1",index=0)
    countries_list = ui.multi_select_all(countries_list, title="Country Selection", key="s2")
    app = ui.single_selector(distinct_apps,title="Select an App", key="s4",include_All=False,index=0)

    selected_date, option = ui.calendar_selector( key="s3", title="Select a date range", index=0)
    daterange = ui.convert_date_to_range(selected_date, option)

if (len(countries_list) and len(daterange) == 2 ):
# --- Cohort Dataframes ---
    user_cohort_df, user_cohort_df_LR = metrics.get_filtered_cohort(app, daterange, language, countries_list)


    def is_compact(apps):
        # Handles string or list
        if isinstance(apps, list):
            return any((a == "Unity" or (isinstance(a, str) and "standalone" in a.lower())) for a in apps if a)
        else:
            a = apps
            return (a == "Unity" or (isinstance(a, str) and "standalone" in a.lower()))

    if is_compact(app):
        funnel_size = "compact"
    else:
        funnel_size = "large"

    # --- Output Section ---

    create_funnels_by_cohort(
        cohort_df=user_cohort_df,         # main progress cohort
        cohort_df_LR=user_cohort_df_LR,   # app_launch cohort for LR only
        key_prefix="s5",
        funnel_size=funnel_size,
        app=app
    )

    csv = ui.convert_for_download(user_cohort_df)
    st.download_button(
        label="Download",
        data=csv,
        file_name="user_cohort_list.csv",
        key="s6",
        icon=":material/download:",
        mime="text/csv",
    )
