import streamlit as st
from rich import print as rprint
from  ui_components import create_funnels_by_cohort,create_engagement_figure
import ui_widgets as ui
from millify import prettify
from metrics import get_funnel_step_counts_for_app,get_filtered_cohort,get_cohort_totals_by_metric
from users import ensure_user_data_initialized,get_language_list,get_country_list
from settings import initialize

initialize()
ensure_user_data_initialized()

ui.display_definitions_table("Data Notes",ui.data_notes)

languages = get_language_list()
countries_list = get_country_list()
distinct_apps = ui.get_apps()

col1, col2, col3, col4 = st.columns(4)

with st.sidebar:
    language = ui.single_selector(languages, title="Select a language", key="s1",index=0)
    countries_list = ui.multi_select_all(countries_list, title="Country Selection", key="s2")
    app = ui.single_selector(distinct_apps,title="Select an App", key="s4",include_All=True,index=0)  
    selected_date, option = ui.calendar_selector( key="s3", title="Select a date range", index=0)
    daterange = ui.convert_date_to_range(selected_date, option)

if (len(countries_list) and len(daterange) == 2 ):
    # --- ALL APPS MODE ---
    if app[0] == "All":
        funnel_size = "compact"  # All will always use compact funnel

        # These match ui_components.funnel_variants["compact"]
        stats = ["LR", "PC", "LA", "RA", "GC"]
        titles = [
            "Learner Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Readers Acquired",
            "Game Completed",
        ]

        # Start totals at zero
        totals = {s: 0 for s in stats}

        # All *real* apps (exclude the synthetic "All" option)
        real_apps = [a for a in distinct_apps if a != "All"]

        for app_name in real_apps:
            # app_name is a string; metrics helper expects same shape
            app_stats, counts = get_funnel_step_counts_for_app(
                app=[app_name],  # keep consistent with existing functions
                daterange=daterange,
                language=language,
                countries_list=countries_list,
                funnel_size=funnel_size,
            )

            # Just in case, only sum the stats we’re actually plotting
            for s in stats:
                if s in counts:
                    totals[s] += counts[s]

        # Build counts in the right order
        funnel_step_counts = [totals[s] for s in stats]
        LR_total = totals.get("LR", 0)
        LA_total = totals.get("LA", 0)
        RA_total = totals.get("RA", 0)
        GC_total = totals.get("GC", 0)

        cols = st.columns(4)
        labels_values = [
            ("Learners Reached", prettify(LR_total)),
            ("Learners Acquired", prettify(LA_total)),
            ("Readers Acquired", prettify(RA_total)),
            ("Game Completed", prettify(GC_total)),
    ]
        tile_colors = ["#DCEAFB", "#E6F4EA", "#FFF5E6", "#FDE7E7"]
        for i, (label, value) in enumerate(labels_values):
            with cols[i]:
                ui.metric_tile(label, value, color=tile_colors[i])
        
        # --- Percentages (same logic as create_funnels_by_cohort) ---
        percent_of_previous = [None]
        for i in range(1, len(funnel_step_counts)):
            prev = funnel_step_counts[i - 1]
            curr = funnel_step_counts[i]
            percent = round(100 * curr / prev, 1) if prev and prev > 0 else None
            percent_of_previous.append(percent)

        percent_of_second = [None, None]
        if len(funnel_step_counts) >= 2 and funnel_step_counts[1]:
            second = funnel_step_counts[1]
            for i in range(2, len(funnel_step_counts)):
                curr = funnel_step_counts[i]
                percent = round(100 * curr / second, 1) if second and second > 0 else None
                percent_of_second.append(percent)
        else:
            percent_of_second += [None] * (len(funnel_step_counts) - 2)

        funnel_data = {
            "Title": titles,
            "Count": funnel_step_counts,
            "PercentOfPrevious": percent_of_previous,
            "PercentOfSecond": percent_of_second,
        }

        fig = create_engagement_figure(
            funnel_data,
            key="s5-funnel-all",
            funnel_size=funnel_size,
        )
        st.plotly_chart(fig, use_container_width=True, key="s5-chart-all")

    # --- SINGLE APP MODE  ---
    else:
        user_cohort_df, user_cohort_df_LR = get_filtered_cohort(
            app=app,
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )

        LR = get_cohort_totals_by_metric(user_cohort_df_LR if user_cohort_df_LR is not None else user_cohort_df, "LR")
        LA = get_cohort_totals_by_metric(user_cohort_df, "LA")
        RA = get_cohort_totals_by_metric(user_cohort_df, "RA")
        GC = get_cohort_totals_by_metric(user_cohort_df, "GC")

        col1.metric("Learners Reached", prettify(LR))
        col2.metric("Learners Acquired", prettify(LA))
        col3.metric("Readers Acquired", prettify(RA))
        col4.metric("Game Completed", prettify(GC))

        if ui.is_compact(app):
            funnel_size = "compact"
        else:
            funnel_size = "large"

        create_funnels_by_cohort(
            cohort_df=user_cohort_df,         # main progress cohort
            cohort_df_LR=user_cohort_df_LR,   # app_launch cohort for LR only
            key_prefix="s5",
            funnel_size=funnel_size,
            app=app,
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
