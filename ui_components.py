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


def stats_by_country_map(daterange, countries_list, app="Both", language="All"):
    option = ui.stats_radio_selector()
    df = metrics.get_country_counts(
        daterange, countries_list, option, app, language=language
    )

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

    country_fig.update_layout(
        height=500,
        margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        #       paper_bgcolor="LightSteelBlue",
    )
    country_fig.update_geos(fitbounds="locations")
    st.plotly_chart(country_fig)


@st.cache_data(ttl="1d")
def campaign_gantt_chart():
    df1 = st.session_state.df_campaigns
    df1["campaign_start_date"] = pd.to_datetime(df1["campaign_start_date"]).dt.date

    # Define the chart start date
    chart_start = dt.datetime.strptime("2023-07-01", "%Y-%m-%d").date()

    # Query the DataFrame
    df1 = df1.query("campaign_start_date > @chart_start")

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
        height=1500,
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
        yaxis=dict(tickfont_size=8),
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
    hovertemp += "<b>Cost: </b> %{customdata[1]:$,.2f}<br>"
    fig.update_traces(hoverinfo="text", hovertemplate=hovertemp)
    fig.update_xaxes(
        tickangle=0, tickfont=dict(family="Rockwell", color="#A9A9A9", size=12)
    )

    st.plotly_chart(
        fig, use_container_width=True
    )  # Display the plotly chart in Streamlit


def top_gpc_bar_chart(daterange, countries_list, app="Both", language="All"):
    df = metrics.get_country_counts(
        daterange, countries_list, "GPP", app, language
    ).head(10)
    df.rename(columns={"country": "Country"}, inplace=True)
    fig = px.bar(
        df, x="Country", y="GPP", color="Country", title="Top 10 Countries by GPP %"
    )
    st.plotly_chart(fig, use_container_width=True)


def top_gca_bar_chart(daterange, countries_list, app="Both", language="All"):
    df = metrics.get_country_counts(
        daterange, countries_list, "GCA", app, language
    ).head(10)
    df.rename(columns={"country": "Country"}, inplace=True)
    fig = px.bar(
        df, x="Country", y="GCA", color="Country", title="Top 10 Countries by GCA %"
    )
    st.plotly_chart(fig, use_container_width=True)


def top_LR_LC_bar_chart(daterange, countries_list, option, app="Both", language="All"):
    df = metrics.get_country_counts(
        daterange, countries_list, str(option), app=app, language=language
    ).head(10)

    title = "Top 10 Countries by " + str(option)
    fig = go.Figure(
        data=[
            go.Bar(name="LR", x=df["country"], y=df["LR"]),
            go.Bar(name="LA", x=df["country"], y=df["LA"]),
        ]
    )
    fig.update_layout(title_text=title)
    st.plotly_chart(fig, use_container_width=True)


def LR_LA_line_chart_over_time(
    daterange, countries_list, option, app="Both", language="All"
):
    df_user_list = metrics.filter_user_data(
        daterange, countries_list, option, app=app, language=language
    )

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


def lrc_scatter_chart():
    df_campaigns = st.session_state.df_campaigns
    countries_list = df_campaigns["country"].unique()
    countries_list = list(countries_list)

    # Convert the numpy array to a Python list

    df_counts = metrics.get_country_counts(
        [dt.datetime(2021, 1, 1).date(), dt.date.today()], countries_list, stat="LR"
    )

    option = st.radio("Select a statistic", ("LRC", "LAC"), index=0, horizontal=True)
    x = "LR" if option == "LRC" else "LA"
    df_campaigns = df_campaigns.groupby("country")["cost"].sum().round(2).reset_index()

    # Merge dataframes on 'country'
    merged_df = pd.merge(df_campaigns, df_counts, on="country", how="right")

    min_value = 1000
    merged_df = merged_df[(merged_df["LR"] > min_value) | (merged_df["LA"] > min_value)]

    # Calculate LRC
    merged_df[option] = (merged_df["cost"] / merged_df[x]).round(2)

    # Fill NaN values in LRC column with 0

    merged_df[option] = merged_df[option].fillna(0)
    scatter_df = merged_df[["country", "cost", option, x]]

    fig = px.scatter(
        scatter_df,
        x=x,
        y=option,
        color="country",
        title="Reach to Cost",
    )
    fig.update_traces(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def spend_by_country_map():

    if "df_campaigns" not in st.session_state:
        return pd.DataFrame()
    else:
        df_campaigns = st.session_state.df_campaigns

    df_campaigns = df_campaigns.groupby("country")["cost"].sum().round(2).reset_index()

    country_fig = px.choropleth(
        df_campaigns,
        locations="country",
        color="cost",
        color_continuous_scale=[
            [0, "rgb(166,206,227, 0.5)"],
            [0.05, "rgb(31,120,180,0.5)"],
            [0.1, "rgb(178,223,138,0.5)"],
            [0.3, "rgb(51,160,44,0.5)"],
            [0.6, "rgb(251,154,153,0.5)"],
            [1, "rgb(227,26,28,0.5)"],
        ],
        height=600,
        projection="natural earth",
        locationmode="country names",
        hover_data={
            "cost": ":$,.2f",
        },
    )

    country_fig.update_geos(fitbounds="locations")
    country_fig.update_layout(
        height=600,
        margin=dict(l=10, r=1, b=10, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(country_fig)


def campaign_funnel_chart():
    df_campaigns = st.session_state.df_campaigns
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


def create_engagement_figure(funnel_data=[], key=""):

    fig = go.Figure(
        go.Funnel(
            y=funnel_data["Title"],
            x=funnel_data["Count"],
            textposition="auto",
            #          textinfo="value+percent initial+percent previous",
            hoverinfo="x+y+text+percent initial+percent previous",
            #           key=key,
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


# Show the count of users max level for each level in the game
def levels_line_chart(daterange, countries_list, app="Both", language="All"):
    df_user_list = metrics.filter_user_data(
        daterange, countries_list, stat="LA", app=app, language=language
    )

    # Group by date, country, and app_language, then count the users
    df = (
        df_user_list.groupby(["max_user_level", "app_language"])
        .size()
        .reset_index(name="count")
    )

    # Calculate percent drop for hover text
    df["percent_drop"] = df.groupby("app_language")["count"].pct_change() * 100

    # Create separate traces for each app_language
    traces = []
    for app_language, data in df.groupby("app_language"):
        trace = go.Scatter(
            x=data["max_user_level"],
            y=data["count"],
            mode="lines+markers",
            name=app_language,
            hovertemplate="Max Level: %{x}<br>Count: %{y}<br>Percent Drop: %{customdata:.2f}%<br>App Language: %{text}",
            customdata=data["percent_drop"],
            text=data["app_language"],  # Include app_language in hover text
        )
        traces.append(trace)

    # Create a Plotly layout
    layout = go.Layout(
        xaxis=dict(title="Levels"),
        yaxis=dict(title="Users"),
        height=500,
    )
    # Create a Plotly figure with all traces
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)
