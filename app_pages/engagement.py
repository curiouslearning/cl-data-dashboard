import streamlit as st
import pandas as pd

from settings import initialize
from users import (
    ensure_user_data_initialized,
    get_language_list,
    get_country_list,
)
import ui_widgets as ui
from millify import prettify

from metrics import (
    get_filtered_cohort,
    get_funnel_step_counts_for_app,
)
from ui_components import (
    stats_by_country_map,
    top_stats_bar_chart,
)

# ==========================================================
#   INIT + DEFINITIONS
# ==========================================================
ui.display_definitions_table("Definitions", ui.level_definitions)
ui.display_definitions_table("Data Notes", ui.data_notes)

initialize()
ensure_user_data_initialized()

# ==========================================================
#   SIDEBAR FILTERS
# ==========================================================
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
    app = ui.single_selector(
        apps, title="Select an App", key="sf-10", include_All=True
    )

# ==========================================================
#   HELPERS
# ==========================================================
def build_metrics_for_single_app(app, daterange, language, countries_list):
    """
    Use the same helper as the App Funnel page so numbers match exactly.
    """
    # get_funnel_step_counts_for_app expects a list for app in your setup
    _, counts = get_funnel_step_counts_for_app(
        app=app,
        daterange=daterange,
        language=language,
        countries_list=countries_list,
        funnel_size="compact",
    )

    return {
        "LR": counts.get("LR", 0),
        "LA": counts.get("LA", 0),
        "RA": counts.get("RA", 0),
        "GC": counts.get("GC", 0),
        "GPP": counts.get("GPP", 0.0),
        "GCA": counts.get("GCA", 0.0),
    }


def build_metrics_for_all_apps(daterange, language, countries_list):
    """
    All-app mode: behaves exactly like the Funnel page's ALL logic.
    Sum LR/LA/RA/GC across all apps; GPP/GCA weighted by LR.
    """
    all_apps = [a for a in ui.get_apps() if a != "All"]

    totals = {"LR": 0, "LA": 0, "RA": 0, "GC": 0}
    weighted_gpp_sum = 0.0
    weighted_gca_sum = 0.0
    total_LR_for_weights = 0

    for app_name in all_apps:
        _, counts = get_funnel_step_counts_for_app(
            app=[app_name],
            daterange=daterange,
            language=language,
            countries_list=countries_list,
            funnel_size="compact",
        )

        LR_i = counts.get("LR", 0)

        for k in ("LR", "LA", "RA", "GC"):
            totals[k] += counts.get(k, 0)

        if LR_i > 0:
            weighted_gpp_sum += counts.get("GPP", 0.0) * LR_i
            weighted_gca_sum += counts.get("GCA", 0.0) * LR_i
            total_LR_for_weights += LR_i

    GPP = weighted_gpp_sum / total_LR_for_weights if total_LR_for_weights > 0 else 0.0
    GCA = weighted_gca_sum / total_LR_for_weights if total_LR_for_weights > 0 else 0.0

    return {
        "LR": totals["LR"],
        "LA": totals["LA"],
        "RA": totals["RA"],
        "GC": totals["GC"],
        "GPP": GPP,
        "GCA": GCA,
    }


def build_combined_cohorts_for_all_apps(daterange, language, countries_list):
    """
    Build combined user_cohort_df and LR_df across all apps so that
    the map and Top 10s truly reflect ALL app usage.

    Returns:
        combined_df, combined_LR_df
    """
    all_apps = [a for a in ui.get_apps() if a != "All"]

    user_rows = []
    lr_rows = []

    for app_name in all_apps:
        this_app = [app_name]
        user_df, user_df_LR = get_filtered_cohort(
            app=this_app,
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )

        if user_df is not None and not user_df.empty:
            df_copy = user_df.copy()
            df_copy["app"] = app_name
            user_rows.append(df_copy)

        if user_df_LR is not None and not user_df_LR.empty:
            lr_copy = user_df_LR.copy()
            lr_copy["app"] = app_name
            lr_rows.append(lr_copy)

    combined_df = (
        pd.concat(user_rows, ignore_index=True) if user_rows else pd.DataFrame()
    )
    combined_LR_df = (
        pd.concat(lr_rows, ignore_index=True) if lr_rows else None
    )

    return combined_df, combined_LR_df


# ==========================================================
#   MAIN CONTENT
# ==========================================================
if len(daterange) == 2 and len(countries_list) > 0:
    date_start = daterange[0].strftime("%Y-%m-%d")
    date_end = daterange[1].strftime("%Y-%m-%d")

    st.markdown("**Selected Range:**")
    st.text(f"{date_start} to {date_end}")

    # ------------------------------------------------------
    # 1) METRICS (match Funnel page)
    # ------------------------------------------------------
    if app[0] == "All":
        stats = build_metrics_for_all_apps(
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )
    else:
        stats = build_metrics_for_single_app(
            app=app,
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )

    # Colored metric tiles
    tile_colors = ["#DCEAFB", "#E6F4EA", "#FFF5E6", "#FDE7E7", "#EFEAFF", "#E8F5FA"]
    rows = [
        ("Learners Reached", prettify(stats["LR"])),
        ("Learners Acquired", prettify(stats["LA"])),
        ("Readers Acquired", prettify(stats["RA"])),
        ("Games Completed", prettify(stats["GC"])),
        ("Game Progress %", f"{stats['GPP']:.2f}%"),
        ("Game Completion Avg", f"{stats['GCA']:.2f}%"),
    ]

    cols = st.columns(3)
    for i, (label, value) in enumerate(rows):
        color = tile_colors[i % len(tile_colors)]
        with cols[i % 3]:
            st.markdown(
                f"""
                <div style="
                    padding:16px;
                    border-radius:16px;
                    background-color:{color};
                    text-align:center;
                    margin-bottom:12px;
                ">
                    <div style="font-size:15px; color:#555;">{label}</div>
                    <div style="font-size:24px; font-weight:700; margin-top:4px;">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ------------------------------------------------------
    # 2) BUILD COHORT DATAFRAMES FOR MAP + TOP 10s
    # ------------------------------------------------------
    if app[0] == "All":
        user_cohort_df, user_cohort_df_LR = build_combined_cohorts_for_all_apps(
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )
    else:
        user_cohort_df, user_cohort_df_LR = get_filtered_cohort(
            app=app,
            daterange=daterange,
            language=language,
            countries_list=countries_list,
        )

    # For CR, LR data comes from separate DF
    if app[0] == "CR":
        LR_df = user_cohort_df_LR
    elif app[0] == "All":
        # In ALL mode, LR_df is the combined LR_df when it exists
        LR_df = user_cohort_df_LR if user_cohort_df_LR is not None else user_cohort_df
    else:
        LR_df = user_cohort_df

    # ------------------------------------------------------
    # 3) WORLD MAP
    # ------------------------------------------------------
    st.divider()
    st.subheader("Engagement across the world")

    map_option = ui.stats_radio_selector()  # e.g., "LR", "LA", "RA", "GC", etc.

    if map_option == "LR" and LR_df is not None:
        df_for_map = LR_df
    else:
        df_for_map = user_cohort_df

    df_download_map = stats_by_country_map(
        user_cohort_df=df_for_map,
        user_cohort_df_LR=LR_df,
        app=app,
        option=map_option,
        min_funnel=True,
        sort_by="Total",
    )

    # ------------------------------------------------------
    # 4) TOP 10s
    # ------------------------------------------------------
    st.divider()
    st.subheader("Top 10's")

    c1, c2 = st.columns(2)
    with c1:
        top_option = st.radio(
            "Select a statistic",
            ("LR", "LA", "RA", "GC", "GPP", "GCA"),
            index=0,
            horizontal=True,
            key="e-3",
        )
    with c2:
        display_category = st.radio(
            "Display by",
            ("Country", "Language"),
            index=0,
            horizontal=True,
            key="e-4",
        )

    if top_option == "LR" and LR_df is not None:
        df_for_bars = LR_df
    else:
        df_for_bars = user_cohort_df

    df_download_top = top_stats_bar_chart(
        user_cohort_df=df_for_bars,
        option=top_option,
        display_category=display_category,
        app=app,
    )

    # ------------------------------------------------------
    # 5) CSV DOWNLOAD
    # ------------------------------------------------------
    csv = ui.convert_for_download(df_download_top)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="top_LR_LC_bar_chart.csv",
        key="e-12",
        icon=":material/download:",
        mime="text/csv",
    )
