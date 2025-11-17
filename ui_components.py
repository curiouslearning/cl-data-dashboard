import streamlit as st
import datetime as dt
from rich import print
import plotly.express as px
import plotly.graph_objects as go
from metrics import get_sorted_funnel_df,funnel_percent_by_group
from millify import prettify


default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]

@st.cache_data(ttl="1d", show_spinner=False)
def stats_by_country_map(
    user_cohort_df,
    user_cohort_df_LR=None,
    app=None,
    option="LR",
    min_funnel=True,
    sort_by="Total",
):
    """
    Draws a choropleth world map showing funnel metrics (LR, LA, RA, etc.)
    by country using the standardized funnel helper for consistency.

    Parameters
    ----------
    user_cohort_df : pd.DataFrame
        Main user cohort dataframe
    user_cohort_df_LR : pd.DataFrame, optional
        Learners Reached dataframe (for CR app only)
    app : str or list, optional
        App name, e.g. "CR" or "Unity"
    option : str, default "LR"
        Which funnel metric to color by ("LR", "LA", "RA", "GC", etc.)
    min_funnel : bool, default True
        If True, use minimal funnel version (CR only)
    sort_by : str, default "Total"
        Sorting behavior ("Total" or "Percent")

    Returns
    -------
    df : pd.DataFrame
        Funnel dataframe by country used to render the map
    """

    # ✅ Use helper for consistent funnel data by country
    df, funnel_steps = get_sorted_funnel_df(
        cohort_df=user_cohort_df,
        cohort_df_LR=user_cohort_df_LR,
        groupby_col="country",
        app=app,
        min_funnel=min_funnel,
        stat=option,
        sort_by=sort_by,
        ascending=False,
        use_top_ten=False,  # include all countries
    )

    # Ensure all expected funnel columns exist
    hover_cols = [c for c in ["LR", "LA", "RA", "GC"] if c in df.columns]

    # Build custom hovertemplate
    hover_lines = []
    hover_lines.append("<b>%{location}</b>")  # Country name first

    if option in df.columns:
        hover_lines.append(
            f"<b>{option}: %{{customdata[{hover_cols.index(option)}]:,}}</b>"
        )

    for c in hover_cols:
        if c != option:
            hover_lines.append(
                f"{c}: %{{customdata[{hover_cols.index(c)}]:,}}"
            )

    hovertemplate = "<br>".join(hover_lines) + "<extra></extra>"

    # Choropleth
    country_fig = px.choropleth(
        df,
        locations="country",
        color=str(option),
        color_continuous_scale=[
            "#F9FAFA",
            "#7ef7f7",
            "#a9b6b5",
            "#d0a272",
            "#e48f35",
            "#a18292",
            "#85526c",
            "#48636e",
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
    )

    # Apply hover formatting
    country_fig.update_traces(
        customdata=df[hover_cols],
        hovertemplate=hovertemplate,
    )

    # Layout cleanup
    country_fig.update_layout(
        height=500,
        margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    country_fig.update_geos(fitbounds="locations")

    st.plotly_chart(country_fig, use_container_width=True)
    return df

def top_stats_bar_chart(
    user_cohort_df,
    user_cohort_df_LR=None,
    app=None,
    option="LA",
    display_category="Country",
    min_funnel=True
):
    """
    Draws a top-10 bar chart by funnel or performance metric.
    Supports dynamic toggle between totals and percentages,
    and auto-formats percentage-based metrics like GPP / GCA.
    """
    groupby_col = "country" if display_category == "Country" else "app_language"

    # --- Determine which metrics are inherently percentages ---
    pct_metrics = ["GPP", "GCA"]

    # --- UI toggle: show percentages instead of totals (only for non-pct metrics) ---
    use_toggle = option not in pct_metrics
    use_percent = False
    if use_toggle:
        use_percent = st.toggle("Show percentages instead of totals", value=False)

    # --- Get funnel data ---
    sort_mode = "Percent" if use_percent else "Total"
    df, funnel_steps = get_sorted_funnel_df(
        cohort_df=user_cohort_df,
        cohort_df_LR=user_cohort_df_LR,
        groupby_col=groupby_col,
        app=app,
        min_funnel=min_funnel,
        stat=option,
        sort_by=sort_mode,
        ascending=False,
        use_top_ten=False,
    )
    
    #save the whole dataframe for download purposes
    df_return = df
    df = df.head(10)

    # --- Pick correct stat column ---
    stat_col = option if option in pct_metrics else (
        f"{option}_pct" if use_percent and f"{option}_pct" in df.columns else option
    )

    # --- Color palette ---
    custom_colors = [
        "#F9FAFA", "#7ef7f7", "#a9b6b5", "#d0a272",
        "#e48f35", "#a18292", "#85526c", "#48636e"
    ]
    color_seq = (custom_colors * 2)[:len(df)]

    # --- Determine if the y-axis is a percentage type ---
    is_percent_metric = option in pct_metrics or use_percent

    # --- Create hover text ---
    hover_template = (
        f"{display_category}: %{{x}}<br>"
        f"{option}: %{{y:.2f}}%<extra></extra>"
        if is_percent_metric
        else f"{display_category}: %{{x}}<br>"
             f"{option}: %{{y:,.0f}}<extra></extra>"
    )

    # --- Create Bar Chart ---
    bar_trace = go.Bar(
        x=df[groupby_col],
        y=df[stat_col],
        marker_color=color_seq,
        text=[
            f"{val:.2f}%" if is_percent_metric else f"{val:,.0f}"
            for val in df[stat_col]
        ],
        textposition="outside",
        hovertemplate=hover_template,
    )

    # --- Smart chart title and axis label ---
    yaxis_label = "Percentage (%)" if is_percent_metric else "Total"
    title_suffix = "%" if is_percent_metric else ""
    chart_title = f"Top 10 {display_category}s by {option}{title_suffix}"

    fig = go.Figure(bar_trace)
    fig.update_layout(
        title=chart_title,
        xaxis_title=display_category,
        yaxis_title=yaxis_label,
        font=dict(size=13),
        margin=dict(l=20, r=10, t=50, b=40),
        showlegend=False,
        barmode="group",
        bargap=0.2,
        bargroupgap=0.0,
        width=650,
        height=500,
    )

    # --- Optional caption for clarity ---
    if use_percent:
        st.caption("Percentages represent each group’s share of LR users.")
    elif option in pct_metrics:
        st.caption(f"{option} is already expressed as a percentage metric.")

    st.plotly_chart(fig, use_container_width=False)
    return df_return


def create_engagement_figure(funnel_data, key="", funnel_size="large"):
    percent_2nd = funnel_data.get("PercentOfSecond", [None] * len(funnel_data["Count"]))

    hovertemplate = []
    for i, (title, count, pct2) in enumerate(zip(funnel_data["Title"], funnel_data["Count"], percent_2nd)):
        pct2_txt = (
            f"<br>% of DC: {pct2:.1f}%"
            if funnel_size == "large" and pct2 is not None else ""
        )
        # Use Plotly's built-in variables for percent of previous and initial
        hovertemplate.append(
            f"<b>{title}</b><br>"
            f"Count: {count:,d}"
            "<br>% of previous: %{percentPrevious:.1%}"
            "<br>% of first: %{percentInitial:.1%}"
            f"{pct2_txt}<extra></extra>"
        )

    fig = go.Figure(
        go.Funnel(
            y=funnel_data["Title"],
            x=funnel_data["Count"],
            textposition="auto",
            marker={
                "color": [
                    "#4F420A", "#73600F", "#947C13", "#E0BD1D",
                    "#B59818", "#D9B61C", "#6C5212", "#8B7121"
                ],
                "line": {
                    "width": [4, 3, 2, 2, 2, 1, 1, 1],
                    "color": ["wheat"] * 8,
                },
            },
            connector={"line": {"color": "#4F3809", "dash": "dot", "width": 3}},
            hovertemplate=hovertemplate,
        )
    )
    fig.update_traces(texttemplate="%{value:,d}")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
def create_funnels_by_cohort(
    cohort_df,
    key_prefix="",
    funnel_size="medium",
    cohort_df_LR=None,
    app=None,
):
    """
    Builds a funnel visualization for the selected cohort and app.
    Uses cached funnel_percent_by_group to compute all step totals at once.
    """

    funnel_variants = {
        "compact": {
            "stats": ["LR", "PC", "LA", "RA", "GC"],
            "titles": [
                "Learner Reached", "Puzzle Completed",
                "Learners Acquired", "Readers Acquired", "Game Completed"
            ],
        },
        "large": {
            "stats": ["LR", "DC", "TS", "SL", "PC", "LA", "RA", "GC"],
            "titles": [
                "Learner Reached", "Download Completed", "Tapped Start",
                "Selected Level", "Puzzle Completed",
                "Learners Acquired", "Readers Acquired", "Game Completed",
            ],
        },
        "medium": {
            "stats": ["DC", "TS", "SL", "PC", "LA", "RA", "GC"],
            "titles": [
                "Download Completed", "Tapped Start", "Selected Level",
                "Puzzle Completed", "Learners Acquired",
                "Readers Acquired", "Game Completed",
            ],
        },
    }

    variant = funnel_variants.get(funnel_size, funnel_variants["medium"])
    stats = variant["stats"]
    titles = variant["titles"]

    # --- Compute all funnel metrics once (cached) ---
    funnel_df, funnel_steps = funnel_percent_by_group(
        cohort_df=cohort_df,
        cohort_df_LR=cohort_df_LR,
        groupby_col="app_language",  # not used for global totals
        app=app,
        min_funnel=(funnel_size == "compact"),
    )

    # --- Aggregate totals across all groups ---
    totals = {s: funnel_df[s].sum() if s in funnel_df.columns else 0 for s in stats}

    funnel_step_counts = [totals.get(stat, 0) for stat in stats]

    # --- Percentages ---
    percent_of_previous = [None]
    for i in range(1, len(funnel_step_counts)):
        prev = funnel_step_counts[i - 1]
        curr = funnel_step_counts[i]
        percent = round(100 * curr / prev, 1) if prev and prev > 0 else None
        percent_of_previous.append(percent)

    percent_of_second = [None, None]
    if len(funnel_step_counts) >= 2 and funnel_step_counts[1]:
        for i in range(2, len(funnel_step_counts)):
            second = funnel_step_counts[1]
            curr = funnel_step_counts[i]
            percent = round(100 * curr / second, 1) if second and second > 0 else None
            percent_of_second.append(percent)
    else:
        percent_of_second += [None] * (len(funnel_step_counts) - 2)

    # --- Build funnel data dict ---
    funnel_data = {
        "Title": titles,
        "Count": funnel_step_counts,
        "PercentOfPrevious": percent_of_previous,
        "PercentOfSecond": percent_of_second,
    }

    # --- Render chart ---
    fig = create_engagement_figure(
        funnel_data,
        key=f"{key_prefix}-funnel",
        funnel_size=funnel_size,
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}-chart")
    
    