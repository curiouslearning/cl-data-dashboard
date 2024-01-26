import streamlit as st
import pandas as pd
import datetime as dt
import calendar
from rich import print
import plost
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import metrics

from dateutil.relativedelta import relativedelta
import users

min_date = dt.datetime(2021, 1, 1).date()
max_date = dt.date.today()


def display_definitions_table():
    expander = st.expander("Definitions")
    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    def_df = pd.DataFrame(
        [
            [
                "LR",
                "Learner Reached",
                "The number of users that downloaded and opened the app",
                "COUNT(Learners Reached)",
            ],
            [
                "LA",
                "Learner Acquisition",
                "The number of users that have completed at least one FTM level.",
                "COUNT(Learners)",
            ],
            [
                "GPC",
                "Game Percent Complete",
                "The percentage of FTM levels completed from total levels",
                "Max Level Reached / Total Levels",
            ],
            [
                "GCC",
                "Game Completion Cost",
                "The cost (USD) associated with one learner completing over 90% of FTM levels.",
                "Total Spend / EstRA * LA",
            ],
            [
                "LAC",
                "Learner Acquisition Cost",
                "The cost (USD) of acquiring one learner.",
                "Total Spend / LA",
            ],
            [
                "RA",
                "Reading Acquisition",
                "",
                "",
            ],
            [
                "RAC",
                "Reading Acquisition Cost",
                "The cost (USD) associated with RA.",
                "Total Spend / (RA*LA)",
            ],
        ],
        columns=["Acronym", "Name", "Definition", "Formula"],
    )
    expander.table(def_df)


def quarter_start(month):
    quarters = [1, 4, 7, 10]
    return (month - 1) // 3 * 3 + 1 if month in quarters else None


def year_selector():
    this_year = dt.datetime.now().year
    report_year = st.sidebar.radio(
        "", range(this_year, this_year - 4, -1), horizontal=True
    )

    return report_year


def month_selector():
    from calendar import month_abbr

    with st.sidebar.expander("Report month"):
        this_year = dt.datetime.now().year
        this_month = dt.datetime.now().month
        report_year = st.sidebar.selectbox("", range(this_year, this_year - 4, -1))
        month_abbr = month_abbr[1:]
        report_month_str = st.sidebar.radio(
            "", month_abbr, index=this_month - 1, horizontal=True
        )
        report_month = month_abbr.index(report_month_str) + 1

    return report_month, report_year


def custom_date_selection():
    # date_range = st.sidebar.date_input("Pick a date", (min_date, max_date))
    today = dt.datetime.now().date()
    last_year = dt.date(today.year, 1, 1) - relativedelta(years=1)

    date_range = st.sidebar.slider(
        label="Select Range:",
        min_value=dt.date(2021, 1, 1),
        value=(last_year, today),
        max_value=today,
    )

    return date_range


def ads_platform_selector():
    platform = st.sidebar.radio(
        label="Ads Platform",
        options=["Facebook", "Google", "Both"],
        horizontal=True,
        index=2,
    )
    return platform


# this is a callback for language_selector
def update_language_session_state():
    if st.session_state.lang_key:
        st.session_state.language = st.session_state.lang_key


# This method uses the key parameter of the selectbox
# to automatically ad the selection to session state.
def language_selector():
    df = users.get_language_list()
    df.insert(0, "All")

    st.session_state.selectbox_value = st.sidebar.selectbox(
        "Select a language",
        df,
        index=0,
        key="lang_key",
        on_change=update_language_session_state,
    )


def multi_select_all(available_options, title):
    available_options.insert(0, "All")
    
    # If a user switches to another page and comes back, selected options is dropped from session state
    # but max_selections still exists.  This has to do with how streamlit handles the key option in widgets
    # This will ensure All is selected when coming back to the page    
    if "selected_options" not in st.session_state:
        st.session_state["selected_options"] = ["All"]
    if "max_selections" not in st.session_state:
        st.session_state["max_selections"] = 1  # Enforce single selection
        st.session_state["selected_options"] = ["All"]  # Set default to "All"

    def options_select():  # Define options_select inside multi_select_all
        if "selected_options" in st.session_state:
            if "All" in st.session_state["selected_options"]:
                st.session_state["selected_options"] = [
                    "All"
                ]  # Reset to "All" if deselected
                st.session_state["max_selections"] = 1  # Enforce single selection again
            else:
                st.session_state["max_selections"] = len(
                    available_options
                )  # Allow multiple selections
        else:
            print("A")

    st.sidebar.multiselect(
        label=title,
        options=available_options,
        key="selected_options",
        max_selections=st.session_state["max_selections"],
        on_change=options_select,  # Pass the function without calling it
        format_func=lambda x: "All" if x == "All" else f"{x}",
    )

    # Display options based on selection state
    if "All" in st.session_state["selected_options"]:
        st.sidebar.write("You selected all options.")
    else:
        st.sidebar.write(
            f"You selected {len(st.session_state['selected_options'])} options: "
        )
        st.sidebar.write(st.session_state["selected_options"])

    return (
        available_options[1:]
        if "All" in st.session_state["selected_options"]
        else st.session_state["selected_options"]
    )  # Return full list if "All" is selected


def calendar_selector():
    option = st.sidebar.radio(
        "Select a report date range",
        ("All time", "Select year", "Select month", "Select custom range"),
        index=0,
    )

    if option == "Select year":
        selected_date = year_selector()
    elif option == "All time":
        selected_date = [min_date, max_date]
    elif option == "Select month":
        selected_date = month_selector()
    else:
        selected_date = custom_date_selection()
    return selected_date, option


def convert_date_to_range(selected_date, option):
    if option == "Select year":
        first = dt.date(selected_date, 1, 1)
        last = dt.date(selected_date, 12, 31)
        return [first, last]
    elif option == "All time":
        return [min_date, max_date]
    elif option == "Select month":
        month = selected_date[0]
        year = selected_date[1]
        first = dt.date(year, month, 1)
        yearmonth = calendar.monthrange(year, month)
        last = dt.date(year, month, yearmonth[1])
        return [first, last]
    else:
        return selected_date


@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df


def paginated_dataframe(df, keys):
    top_menu = st.columns(3)
    with top_menu[0]:
        sort = st.radio(
            "Sort Data", options=["Yes", "No"], horizontal=1, index=1, key=keys[0]
        )
    if sort == "Yes":
        with top_menu[1]:
            sort_field = st.selectbox("Sort By", options=df.columns, key=keys[1])
        with top_menu[2]:
            sort_direction = st.radio(
                "Direction", options=["⬆️", "⬇️"], horizontal=True, key=keys[2]
            )
        df = df.sort_values(
            by=sort_field, ascending=sort_direction == "⬆️", ignore_index=True
        )

    pagination = st.container()
    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox(
            "Page Size", options=[25, 50, 100], key=keys[3], index=1
        )
    with bottom_menu[1]:
        total_pages = int(len(df) / batch_size) if int(len(df) / batch_size) > 0 else 1
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1, key=keys[4]
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")

    pages = split_frame(df, batch_size)
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)


def top_campaigns_by_downloads_barchart(n):
    df_all = st.session_state.df_all
    df = df_all.filter(["campaign_name", "mobile_app_install"], axis=1)
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


def stats_by_country_map(daterange, countries_list):
    option = st.radio(
        "Select a statistic", ("LR", "LA", "GPC"), index=0, horizontal=True
    )
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
    df_user_list = st.session_state.df_user_list
    df1 = df_all.query("@daterange[0] <= day <= @daterange[1]")

    # We only need any row for each campaign
    df1.drop_duplicates(subset="campaign_name", inplace=True)
    df2 = df_user_list.query("@daterange[0] <= first_open <= @daterange[1]")

    # Converting columns to datetime format
    df1["start_date"] = pd.to_datetime(df1["campaign_start_date"])
    df1["end_date"] = pd.to_datetime(df1["campaign_end_date"])

    # If campaign end dates are past today, set it to today for the chart
    d = pd.to_datetime(dt.date.today())
    df1.loc[df1["end_date"] > d, "end_date"] = d

    df1["campaign_name"] = df1["campaign_name"].str[
        :20
    ]  # cut the title to fit the chart
    df2["first_open"] = pd.to_datetime(df2["first_open"])

    # Initializing the count column with zeros
    df1["count"] = 0

    # Iterating over df1 rows and updating the count column
    for index, row in df1.iterrows():
        mask = df2.query(
            "(@df2.first_open >= @row.start_date) & (@df2.first_open <= @row.end_date)"
        )
        df1.at[index, "count"] = len(mask)

    df1 = df1[df1["count"] > 0]  # Eliminate campaigns that didn't get any opens

    df1 = df1[
        (df1["end_date"] - df1["start_date"]).dt.days > 1
    ]  # eliminate campaigns that didn't run longer than a day

    fig = px.timeline(
        df1,
        x_start="start_date",
        x_end="end_date",
        y="campaign_name",
        #        color="count",
    )

    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        title="",
        hoverlabel_bgcolor="#DAEEED",
        bargap=0.2,
        height=600,
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

    fig.update_xaxes(
        tickangle=0, tickfont=dict(family="Rockwell", color="#A9A9A9", size=12)
    )

    st.plotly_chart(
        fig, use_container_width=True
    )  # Display the plotly chart in Streamlit


def top_gpc_bar_chart(daterange, countries_list):
    df = metrics.get_country_counts(daterange, countries_list, "GPC").head(10)
    df.rename(columns={"country": "Country"}, inplace=True)
    fig = px.bar(
        df, x="Country", y="GPC", color="GPC", title="Top 10 Countries by GPC %"
    )
    st.plotly_chart(fig, use_container_width=True)


def top_LR_LC_bar_chart(daterange, countries_list):
    option = st.radio("Select a statistic", ("LR", "LA"), index=0, horizontal=True)
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


def LR_LA_line_chart_over_time(daterange, countries_list):
    option = st.radio(
        "Select a statistic", ("LR", "LA"), index=0, horizontal=True, key="A"
    )
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

    # Plotly line graph
    fig = px.line(
        grouped_df,
        x=groupby,
        y=option,
        color="country",
        markers=True,
        title=title,
    )

    st.plotly_chart(fig, use_container_width=True)
