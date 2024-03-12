import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
import users
import plotly.express as px
import plotly.graph_objects as go
import metrics
from millify import prettify
import ui_widgets as ui

min_date = dt.datetime(2021, 1, 1).date()
max_date = dt.date.today()


def stats_by_country_map(daterange, countries_list):
    option = ui.stats_radio_selector()
    df = metrics.get_country_counts(daterange, countries_list, option)

    country_fig = px.choropleth(
        df,
        locations="country",
        color=str(option),
        color_continuous_scale=[
            "#1584A3",
            "#DB830F",
            "#E6DF15",
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
    )
    country_fig.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
    country_fig.update_geos(fitbounds="locations")
    st.plotly_chart(country_fig)


@st.cache_data(ttl="1d")
def campaign_gantt_chart(daterange):
    df_all = st.session_state.df_all
    df1 = df_all.query("@daterange[0] <= day <= @daterange[1] and source == 'Facebook'")

    # set the cost value in each row to the total cost for that campaign
    df1 = (
        df1.groupby(["campaign_name", "campaign_start_date", "campaign_end_date"])[
            "cost"
        ]
        .sum()
        .reset_index()
    )
    # We only need any row for each campaign
    df1.drop_duplicates(subset="campaign_name", inplace=True)

    # Converting columns to datetime format
    df1["start_date"] = pd.to_datetime(df1["campaign_start_date"])
    df1["end_date"] = pd.to_datetime(df1["campaign_end_date"])

    # If campaign end dates are past today, set it to today for the chart
    d = pd.to_datetime(dt.date.today())
    df1.loc[df1["end_date"] > d, "end_date"] = d

    df1["campaign_name_short"] = df1["campaign_name"].str[
        :20
    ]  # cut the title to fit the chart

    df1 = df1[
        (df1["end_date"] - df1["start_date"]).dt.days > 1
    ]  # eliminate campaigns that didn't run longer than a day

    fig = px.timeline(
        df1,
        x_start="start_date",
        x_end="end_date",
        y="campaign_name_short",
        height=900,
        color_continuous_scale=[
            [0, "rgb(166,206,227, 0.5)"],
            [0.05, "rgb(31,120,180,0.5)"],
            [0.1, "rgb(178,223,138,0.5)"],
            [0.3, "rgb(51,160,44,0.5)"],
            [0.6, "rgb(251,154,153,0.5)"],
            [1, "rgb(227,26,28,0.5)"],
        ],
        color_discrete_sequence=px.colors.qualitative.Vivid,
        color="cost",
        custom_data=[df1["campaign_name"], df1["cost"]],
    )

    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        title="",
        hoverlabel_bgcolor="#DAEEED",
        bargap=0.2,
        xaxis_title="",
        yaxis_title="",
        title_x=0.5,  # Make title centered
        xaxis=dict(
            tickfont_size=10,
            tickangle=270,
            rangeslider_visible=False,
            side="top",  # Place the tick labels on the top of the chart
            showgrid=True,
            zeroline=True,
            showline=True,
            showticklabels=True,
            tickformat="%x\n",
        ),
    )
    hovertemp = "<b>Date: </b> %{x} <br>"
    hovertemp += "<b>Campaign: </b> %{customdata[0]} <br>"
    hovertemp += "<b>Cost: </b> %{customdata[1]} <br>"
    fig.update_traces(hoverinfo="text", hovertemplate=hovertemp)
    fig.update_xaxes(
        tickangle=0, tickfont=dict(family="Rockwell", color="#A9A9A9", size=12)
    )

    st.plotly_chart(
        fig, use_container_width=True
    )  # Display the plotly chart in Streamlit


def top_gpc_bar_chart(daterange, countries_list):
    df = metrics.get_country_counts(daterange, countries_list, "GPP").head(10)
    df.rename(columns={"country": "Country"}, inplace=True)
    fig = px.bar(
        df, x="Country", y="GPP", color="Country", title="Top 10 Countries by GPP %"
    )
    st.plotly_chart(fig, use_container_width=True)


def top_gca_bar_chart(daterange, countries_list):
    df = metrics.get_country_counts(daterange, countries_list, "GCA").head(10)
    df.rename(columns={"country": "Country"}, inplace=True)
    fig = px.bar(
        df, x="Country", y="GCA", color="Country", title="Top 10 Countries by GCA %"
    )
    st.plotly_chart(fig, use_container_width=True)


def top_LR_LC_bar_chart(daterange, countries_list, option):
    df = metrics.get_country_counts(daterange, countries_list, str(option)).head(10)

    title = "Top 10 Countries by " + str(option)
    fig = go.Figure(
        data=[
            go.Bar(name="LR", x=df["country"], y=df["LR"]),
            go.Bar(name="LA", x=df["country"], y=df["LA"]),
        ]
    )
    fig.update_layout(title_text=title)
    st.plotly_chart(fig, use_container_width=True)


def LR_LA_line_chart_over_time(daterange, countries_list, option):
    df_user_list = metrics.filter_user_data(daterange, countries_list, option)
    if option == "LA":
        groupby = "LA Date"
        title = "Daily Learners Acquired"
        df_user_list.rename({"la_date": "LA Date"}, axis=1, inplace=True)
    else:
        groupby = "LR Date"
        title = "Daily Learners Reached"
        df_user_list.rename({"first_open": "LR Date"}, axis=1, inplace=True)

    # Group by date and country, then count the users
    grouped_df = (
        df_user_list.groupby([groupby, "country"]).size().reset_index(name=option)
    )
    grouped_df["7 Day Rolling Mean"] = grouped_df[option].rolling(14).mean()

    # Plotly line graph
    fig = px.line(
        grouped_df,
        x=groupby,
        y=option,
        color="country",
        markers=False,
        title=title,
    )

    st.plotly_chart(fig, use_container_width=True)


def lrc_scatter_chart(daterange):
    countries_list = users.get_country_list()
    df_counts = metrics.get_country_counts(daterange, countries_list, "LR")
    if "df_all" not in st.session_state:
        return pd.DataFrame()
    else:
        df_campaigns = st.session_state.df_all

    option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
    x = "LR" if option == "LRC" else "LA"
    df_campaigns = df_campaigns.groupby("country")["cost"].sum().round(2).reset_index()

    # Merge dataframes on 'country'
    merged_df = pd.merge(df_campaigns, df_counts, on="country", how="right")

    # Calculate LRC
    merged_df[option] = (merged_df["cost"] / merged_df[x]).round(2)

    # Fill NaN values in LRC column with 0
    merged_df[option].fillna(0, inplace=True)

    scatter_df = merged_df[["country", "cost", option, x]]

    fig = px.scatter(
        scatter_df,
        x=x,
        y=option,
        color="country",
        title="Reach to Cost",
    )
    fig.update_traces(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def spend_by_country_map():

    if "df_all" not in st.session_state:
        return pd.DataFrame()
    else:
        df_campaigns = st.session_state.df_all

    df_campaigns = df_campaigns.groupby("country")["cost"].sum().round(2).reset_index()
    country_fig = px.choropleth(
        df_campaigns,
        locations="country",
        color="cost",
        color_continuous_scale=[
            "#1584A3",
            "#DB830F",
            "#E6DF15",
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
    )
    country_fig.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
    country_fig.update_geos(fitbounds="locations")
    st.plotly_chart(country_fig)


def campaign_funnel_chart():
    df_campaigns = st.session_state.df_all
    impressions = df_campaigns["impressions"].sum()

    clicks = df_campaigns["clicks"].sum()

    funnel_data = {
        "Title": [
            "Impressions",
            "Clicks",
        ],
        "Count": [impressions, clicks],
    }

    fig = create_engagement_figure(funnel_data=funnel_data)
    fig.update_layout(
        height=200,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_engagement_figure(daterange=[], countries_list=[], funnel_data=[]):

    fig = go.Figure(
        go.Funnel(
            y=funnel_data["Title"],
            x=funnel_data["Count"],
            textposition="auto",
            textinfo="value+percent initial",
            # opacity=0.65,
            marker={
                "color": [
                    "#4F420A",
                    "#73600F",
                    "#947C13",
                    "#E0BD1D",
                    "#B59818",
                    "#D9B61C",
                ],
                "line": {
                    "width": [4, 3, 2, 2, 2, 1],
                    "color": ["wheat", "wheat", "wheat", "wheat"],
                },
            },
            connector={"line": {"color": "#4F3809", "dash": "dot", "width": 3}},
        )
    )
    fig.update_traces(texttemplate="%{value:,d}")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def engagement_funnel_chart():
    ui.language_selector()  # puts selection in session state
    countries_list = users.get_country_list()
    countries_list = ui.multi_select_all(
        countries_list, title="Country Selection", key="funnel_key"
    )

    selected_date, option = ui.calendar_selector()
    daterange = ui.convert_date_to_range(selected_date, option)
    LR = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    PC = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    LA = metrics.get_totals_by_metric(daterange, countries_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, countries_list, "GC")
    funnel_data = {
        "Title": [
            "Learners Reached",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }

    fig = create_engagement_figure(daterange, countries_list, funnel_data)

    st.plotly_chart(fig, use_container_width=True)


def engagement_funnel_chart_compare():

    ui.language_selector()  # puts selection in session state
    countries_list = users.get_country_list()
    countries_list = ui.multi_select_all(
        countries_list, title="Country Selection", key="funnel_compare_key"
    )

    selected_date, option = ui.calendar_selector()
    daterange = ui.convert_date_to_range(selected_date, option)

    col1, col2 = st.columns(2)
    col1.subheader("Unity")
    col2.subheader("Curious Reader")

    st.session_state.app = "Unity"
    LR = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    PC = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    #  TS = metrics.get_totals_by_metric(daterange, countries_list, "TS")
    #  SL = metrics.get_totals_by_metric(daterange, countries_list, "SL")
    LA = metrics.get_totals_by_metric(daterange, countries_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, countries_list, "GC")

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Tapped Start",
            "Selected Level",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }
    fig = create_engagement_figure(daterange, countries_list, funnel_data)
    col1.plotly_chart(fig, use_container_width=True)

    st.session_state.app = "CR"
    LR = metrics.get_totals_by_metric(daterange, countries_list, stat="LR")
    PC = metrics.get_totals_by_metric(daterange, countries_list, "PC")
    #   TS = metrics.get_totals_by_metric(daterange, countries_list, "TS")
    #   SL = metrics.get_totals_by_metric(daterange, countries_list, "SL")
    LA = metrics.get_totals_by_metric(daterange, countries_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, countries_list, "GC")

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Tapped Start",
            "Selected Level",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, PC, LA, GC],
    }

    fig = create_engagement_figure(daterange, countries_list, funnel_data)
    col2.plotly_chart(fig, use_container_width=True)


def cr_funnel_chart_details():

    daterange = [dt.date(2024, 3, 5), pd.to_datetime("today").date()]
    country_list = users.get_country_list()

    st.subheader("Curious Reader Acquisition Starting March 5th, 2024")

    st.session_state.app = "CR"
    LR = metrics.get_totals_by_metric(daterange, country_list, stat="LR")
    LA = metrics.get_totals_by_metric(daterange, country_list, stat="LA")
    GC = metrics.get_totals_by_metric(daterange, country_list, "GC")

    df = metrics.get_cr_event_counts()
    PC = int(df.tail(1)["puzzle_completed"])
    TS = int(df.tail(1)["tapped_start"])
    SL = int(df.tail(1)["selected_level"])

    funnel_data = {
        "Title": [
            "Learners Reached",
            "Tapped Start",
            "Selected Level",
            "Puzzle Completed",
            "Learners Acquired",
            "Game Completed",
        ],
        "Count": [LR, TS, SL, PC, LA, GC],
    }

    fig = create_engagement_figure(daterange, country_list, funnel_data)
    st.plotly_chart(fig, use_container_width=True)
