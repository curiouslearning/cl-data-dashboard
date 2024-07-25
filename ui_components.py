import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
import plotly.express as px
import plotly.graph_objects as go
import metrics
from millify import prettify
import ui_widgets as ui
import numpy as np
import plost
import users

default_daterange = [dt.datetime(2021, 1, 1).date(), dt.date.today()]

@st.cache_data(ttl="1d", show_spinner=False)
def stats_by_country_map(daterange, countries_list, app="Both", language="All", option="LR"):

    df = metrics.get_counts(type="country",
    daterange=daterange, countries_list=countries_list, app=app, language=language
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
        hover_data={
            "LR": ":,",
            "PC": ":,",
            "LA": ":,",
            "GPP": ":,",
            "GCA": ":,",
        },
    )

    country_fig.update_layout(
        height=500,
        margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        #       paper_bgcolor="LightSteelBlue",
    )

    country_fig.update_geos(fitbounds="locations")
    st.plotly_chart(country_fig)


@st.cache_data(ttl="1d", show_spinner=False)
def campaign_gantt_chart(daterange):
    
    df1 = st.session_state.df_campaigns
    df1["campaign_start_date"] = pd.to_datetime(df1["campaign_start_date"]).dt.date

    # Define the chart start date
    chart_start = daterange[0]

    # Query the DataFrame
    df1 = df1.query("campaign_start_date > @chart_start")

    # Converting columns to datetime format
    df1["start_date"] = pd.to_datetime(df1["campaign_start_date"])
    df1["end_date"] = pd.to_datetime(df1["campaign_end_date"])

    # Remove rows where 'end_date' is greater than one year from today (likely invalid campaign)
    today = dt.datetime.now()
    one_year_from_today = today + dt.timedelta(days=365)
    df1 = df1[df1["end_date"] <= one_year_from_today]


    df1["campaign_name_short"] = df1["campaign_name"].str[
        :20
    ]  # cut the title to fit the chart

    df1 = df1[
        (df1["end_date"] - df1["start_date"]).dt.days > 1
    ]  # eliminate campaigns that didn't run longer than a day
    rows = len(df1.index)

    fontsize = 8
    if rows > 80:
        height = rows * 10
    elif rows > 40 and rows <= 80:
        height = rows * 20
    elif  rows > 10 and rows <= 40:
        height = rows * 30
        fontsize = 12
    else:
        height = 500
        fontsize = 18


    fig = px.timeline(
        df1,
        x_start="start_date",
        x_end="end_date",
        y="campaign_name_short",
        height=height,
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
        yaxis=dict(tickfont_size=fontsize),
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

@st.cache_data(ttl="1d", show_spinner=False)
def top_gpp_bar_chart(daterange, countries_list, app="Both", language="All",display_category="Country"):

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"     

    df = metrics.get_counts(type=display_group,
    daterange=daterange, countries_list=countries_list, app=app, language=language
    )
    
    df = df[[display_group, "GPP"]].sort_values(by="GPP", ascending=False).head(10)

    fig = px.bar(
        df, x=display_group, y="GPP", color=display_group, title="Top 10 Countries by GPP %"
    )
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def top_gca_bar_chart(daterange, countries_list, app="Both", language="All",display_category="Country"):

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"     
    
    df = metrics.get_counts(type=display_group,
        daterange=daterange, countries_list=countries_list, app=app, language=language
    )

    df = df[[display_group, "GCA"]].sort_values(by="GCA", ascending=False).head(10)

    fig = px.bar(
        df,
        x=display_group,
        y="GCA",
        color=display_group,
        title="Top 10  by GCA %",
    )
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def top_LR_LC_bar_chart(daterange, countries_list, option, app="Both", language="All",display_category="Country"):
    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"      

    df = metrics.get_counts(type=display_group,
        daterange=daterange, countries_list=countries_list, app=app, language=language
    )


    df = (
        df[[display_group, "LR", "LA"]]
        .sort_values(by=option, ascending=False)
        .head(10)
        .round(2)
    )

    title = "Top 10 by " + str(option)
    fig = go.Figure(
        data=[
            go.Bar(
                name="LR",
                x=df[display_group],
                y=df["LR"],
                hovertemplate=" %{x}<br>LR: %{y:,.0f}<extra></extra>",
            ),
            go.Bar(
                name="LA",
                x=df[display_group],
                y=df["LA"],
                hovertemplate=" %{x}<br>LA: %{y:,.0f}<extra></extra>",
            ),
        ],
    )
    fig.update_layout(title_text=title)
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def LR_LA_line_chart_over_time(
    daterange, countries_list, option, app="Both", language="All",display_category="Country"
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

    # Group by date and display_type, then count the users
    if display_category == "Country":
        display_group = "country"
    elif display_category == "Language":
        display_group = "app_language"      
        
    grouped_df = (df_user_list.groupby([groupby, display_group]).size().reset_index(name=option))
    grouped_df["7 Day Rolling Mean"] = grouped_df[option].rolling(14).mean()

    # Plotly line graph
    fig = px.line(
        grouped_df,
        x=groupby,
        y=option,
        color=display_group,
        markers=False,
        title=title,
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def lrc_scatter_chart(daterange,option,display_category):
    df_campaigns = st.session_state.df_campaigns

    if display_category == "Country":
        display_group = "country"
        countries_list = df_campaigns["country"].unique()
        countries_list = list(countries_list)
        df_counts = metrics.get_counts(
            daterange=daterange,type=display_group,countries_list=countries_list
        )
    elif display_category == "Language":
        display_group = "app_language"   
        language =  df_campaigns["app_language"].unique()  
        language = list(language)
        df_counts = metrics.get_counts(
            daterange=daterange,type=display_group,language=language
        )

    x = "LR" if option == "LRC" else "LA"
    df_campaigns = df_campaigns.groupby(display_group)["cost"].sum().round(2).reset_index()

    # Merge dataframes on 'country'
    merged_df = pd.merge(df_campaigns, df_counts, on=display_group, how="right")
    if merged_df.empty:
        st.write("No data")
        return

    min_value = 200
    merged_df = merged_df[(merged_df["LR"] > min_value) | (merged_df["LA"] > min_value)]

    # Calculate LRC
    merged_df[option] = (merged_df["cost"] / merged_df[x]).round(2)

    # Fill NaN values in LRC column with 0
    merged_df[option] = merged_df[option].fillna(0)
    scatter_df = merged_df[[display_group, "cost", option, x]]
    scatter_df["cost"] = "$" + scatter_df["cost"].apply(lambda x: "{:,.2f}".format(x))
    scatter_df[option] = "$" + scatter_df[option].apply(lambda x: "{:,.2f}".format(x))
    scatter_df[x] = scatter_df[x].apply(lambda x: "{:,}".format(x))

    fig = px.scatter(
        scatter_df,
        x=x,
        y=option,
        color=display_group,
        title="Reach to Cost",
        hover_data={
            "cost": True,
            option: ":$,.2f",
            x: ":,",
        },
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data(ttl="1d", show_spinner=False)
def spend_by_country_map(daterange):

    if "df_campaigns_all" not in st.session_state:
        return pd.DataFrame()
    else:
        df_campaigns = st.session_state.df_campaigns_all

    conditions = [
        f"@daterange[0] <= segment_date <= @daterange[1]",
    ]

    query = " and ".join(conditions)
    df_campaigns = df_campaigns.query(query)

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


@st.cache_data(ttl="1d", show_spinner=False)
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
@st.cache_data(ttl="1d", show_spinner=False)
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


@st.cache_data(ttl="1d", show_spinner=False)
def funnel_change_line_chart(
    daterange=default_daterange, languages=["All"], countries_list=["All"], toggle=""
):
    weeks = metrics.weeks_since(daterange)
    weeks = 1 if weeks == 0 else weeks

    for i in range(1, weeks + 1):
        end_date = dt.datetime.now().date()
        start_date = dt.datetime.now().date() - dt.timedelta(i * 7)
        daterange = [start_date, end_date]

        df = metrics.build_funnel_dataframe(
            index_col="start_date",
            daterange=daterange,
            languages=languages,
            countries_list=countries_list,
        )

    df = metrics.add_level_percents(df)

    if toggle == "Compare to Previous":

        df2 = df[
            [
                "start_date",
                "DC over LR",
                "TS over DC",
                "SL over TS",
                "PC over SL",
                "LA over PC",
                "GC over LA",
            ]
        ]
    else:
        df2 = df[
            [
                "start_date",
                "DC over LR",
                "TS over LR",
                "SL over LR",
                "PC over LR",
                "LA over LR",
                "GC over LR",
            ]
        ]

    df2["start_date"] = pd.to_datetime(df2["start_date"])

    # Create traces for each column
    traces = []
    for column in df2.columns[1:]:
        traces.append(
            go.Scatter(
                x=df2["start_date"],
                y=df2[column],
                mode="lines+markers",
                name=column,
                hovertemplate="%{y}%<br>",
            )
        )

    # Create layout
    layout = go.Layout(
        title="Line Chart",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Percent"),
    )

    # Create figure
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def top_campaigns_by_downloads_barchart(n):
    df_campaigns = st.session_state.df_campaigns
    df = df_campaigns.filter(["campaign_name", "mobile_app_install"], axis=1)
    pivot_df = pd.pivot_table(
        df, index=["campaign_name"], aggfunc={"mobile_app_install": "sum"}
    )

    df = pivot_df.sort_values(by=["mobile_app_install"], ascending=False)
    df.reset_index(inplace=True)
    df = df.rename(
        columns={"campaign_name": "Campaign", "mobile_app_install": "Installs"}
    )
    df = df.head(n)
    plost.bar_chart(
        data=df,
        bar="Installs",
        value="Campaign",
        direction="vertical",
        use_container_width=True,
        legend="bottom",
    )


@st.cache_data(ttl="1d", show_spinner=False)
def funnel_change_by_language_chart(
    languages, countries_list, daterange, upper_level, bottom_level
):

    weeks = metrics.weeks_since(daterange)
    end_date = dt.datetime.now().date()

    # Precompute date ranges
    date_ranges = [
        (end_date - dt.timedelta(i * 7), end_date - dt.timedelta((i - 1) * 7))
        for i in range(1, weeks + 1)
    ]

    df = pd.DataFrame(columns=["start_date"] + languages)

    for start_date, end_date in date_ranges:
        daterange = [start_date, end_date]
        df.loc[len(df), "start_date"] = start_date

        for language in languages:
            language_list = [language]
            bottom_level_value = metrics.get_totals_by_metric(
                daterange,
                stat=bottom_level,
                language=language_list,
                countries_list=countries_list,
                app="CR",
            )
            upper_level_value = metrics.get_totals_by_metric(
                daterange,
                stat=upper_level,
                language=language_list,
                countries_list=countries_list,
                app="CR",
            )
            try:
                percentage = round((bottom_level_value / upper_level_value) * 100, 2)
            except ZeroDivisionError:
                percentage = 0
            df.loc[df["start_date"] == start_date, language] = percentage

    # Create traces for each column provided it has a value
    traces = [
        go.Scatter(
            x=df["start_date"],
            y=df[column],
            mode="lines+markers",
            name=column,
            hovertemplate="%{y}%<br>",
        )
        for column in df.columns[1:]
    ]

    # Create layout
    layout = go.Layout(
        title="",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Percent of upper level"),
        legend={"traceorder": "normal"},
    )

    # Create figure
    fig = go.Figure(data=traces, layout=layout)
    fig.update_layout(
        margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def top_tilted_funnel(languages, countries_list, daterange, option):

    df = metrics.build_funnel_dataframe(
        index_col="language",
        daterange=daterange,
        languages=languages,
        countries_list=countries_list,
    )

    fig = go.Figure()

    # Adding each metric as a bar
    levels = ["LR", "DC", "TS", "PC", "LA", "GC"]
    for level in levels:
        fig.add_trace(go.Bar(x=df["language"], y=df[level], name=level))

    title = ""
    fig.update_layout(
        barmode="group",
        title="Language Metrics",
        xaxis_title="Language",
        yaxis_title="Total",
        legend_title="Levels",
        template="plotly_white",
        title_text=title,
        #    margin=dict(l=10, r=1, b=0, t=10, pad=4),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl="1d", show_spinner=False)
def bottom_languages_per_level(selection):
    if selection == "Top performing":
        ascending = False
    else:
        ascending = True
    
    languages = users.get_language_list()
    df = metrics.build_funnel_dataframe(index_col="language", languages=languages)
    # Remove anything where Learners Reached = 0
    df = df[df["LR"] != 0]

    df = metrics.add_level_percents(df)

    dfDCLR = (
        df.sort_values(by="DC over LR", ascending=ascending)
        .head(10)
        .loc[:, ["DC over LR", "language"]]
    ).reset_index(drop=True)

    dfTSDC = (
        df.sort_values(by="TS over DC", ascending=ascending)
        .head(10)
        .loc[:, ["TS over DC", "language"]]
    ).reset_index(drop=True)
    dfSLTS = (
        df.sort_values(by="SL over TS", ascending=ascending)
        .head(10)
        .loc[:, ["SL over TS", "language"]]
    ).reset_index(drop=True)
    dfPCSL = (
        df.sort_values(by="PC over SL", ascending=ascending)
        .head(10)
        .loc[:, ["PC over SL", "language"]]
    ).reset_index(drop=True)
    dfLAPC = (
        df.sort_values(by="LA over PC", ascending=ascending)
        .head(10)
        .loc[:, ["LA over PC", "language"]]
    ).reset_index(drop=True)

    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 16px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    col0, col1, col2, col3, col4, col5, = st.columns(6)

    with col0:
        st.caption("Download Completed")
        st.caption("")
        st.caption("Tapped Start")
        st.caption("")
        st.caption("Selected Level")
        st.caption("")
        st.caption("Puzzle Completed")
        st.caption("")
        st.caption("Learner Acquired")
        st.caption("")
        st.caption("Game Completed")
    with col1:
        st.metric(label=dfDCLR["language"].loc[0], value=f"{dfDCLR["DC over LR"].loc[0]:.2f}%")
        st.metric(label=dfTSDC["language"].loc[0], value=f"{dfTSDC["TS over DC"].loc[0]:.2f}%")
        st.metric(label=dfSLTS["language"].loc[0], value=f"{dfSLTS["SL over TS"].loc[0]:.2f}%")
        st.metric(label=dfPCSL["language"].loc[0], value=f"{dfPCSL["PC over SL"].loc[0]:.2f}%")
        st.metric(label=dfLAPC["language"].loc[0], value=f"{dfLAPC["LA over PC"].loc[0]:.2f}%")
    with col2:
        st.metric(label=dfDCLR["language"].loc[1], value=f"{dfDCLR["DC over LR"].loc[1]:.2f}%")
        st.metric(label=dfTSDC["language"].loc[1], value=f"{dfTSDC["TS over DC"].loc[1]:.2f}%")
        st.metric(label=dfSLTS["language"].loc[1], value=f"{dfSLTS["SL over TS"].loc[1]:.2f}%")
        st.metric(label=dfPCSL["language"].loc[1], value=f"{dfPCSL["PC over SL"].loc[1]:.2f}%")
        st.metric(label=dfLAPC["language"].loc[1], value=f"{dfLAPC["LA over PC"].loc[1]:.2f}%")
    with col3:
        st.metric(label=dfDCLR["language"].loc[2], value=f"{dfDCLR["DC over LR"].loc[2]:.2f}%")
        st.metric(label=dfTSDC["language"].loc[2], value=f"{dfTSDC["TS over DC"].loc[2]:.2f}%")
        st.metric(label=dfSLTS["language"].loc[2], value=f"{dfSLTS["SL over TS"].loc[2]:.2f}%")
        st.metric(label=dfPCSL["language"].loc[2], value=f"{dfPCSL["PC over SL"].loc[2]:.2f}%")
        st.metric(label=dfLAPC["language"].loc[2], value=f"{dfLAPC["LA over PC"].loc[2]:.2f}%")
    with col4:
        st.metric(label=dfDCLR["language"].loc[3], value=f"{dfDCLR["DC over LR"].loc[3]:.2f}%")
        st.metric(label=dfTSDC["language"].loc[3], value=f"{dfTSDC["TS over DC"].loc[3]:.2f}%")
        st.metric(label=dfSLTS["language"].loc[3], value=f"{dfSLTS["SL over TS"].loc[3]:.2f}%")
        st.metric(label=dfPCSL["language"].loc[3], value=f"{dfPCSL["PC over SL"].loc[3]:.2f}%")
        st.metric(label=dfLAPC["language"].loc[3], value=f"{dfLAPC["LA over PC"].loc[3]:.2f}%")
    with col5:
        st.metric(label=dfDCLR["language"].loc[4], value=f"{dfDCLR["DC over LR"].loc[4]:.2f}%")
        st.metric(label=dfTSDC["language"].loc[4], value=f"{dfTSDC["TS over DC"].loc[4]:.2f}%")
        st.metric(label=dfSLTS["language"].loc[4], value=f"{dfSLTS["SL over TS"].loc[4]:.2f}%")
        st.metric(label=dfPCSL["language"].loc[4], value=f"{dfPCSL["PC over SL"].loc[4]:.2f}%")
        st.metric(label=dfLAPC["language"].loc[4], value=f"{dfLAPC["LA over PC"].loc[4]:.2f}%")

 
 
