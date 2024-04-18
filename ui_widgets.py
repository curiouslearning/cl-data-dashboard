import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
from dateutil.relativedelta import relativedelta
import users
import calendar
import plost

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
                "PC",
                "Puzzle Complete / Drgged a Stone",
                "The number of users that have completed at least one puzzle",
                "",
            ],
            [
                "LA",
                "Learner Acquisition",
                "The number of users that have completed at least one FTM level.",
                "COUNT(Learners Acquired)",
            ],
            [
                "GPP",
                "Game Progress Percent",
                "The percentage of FTM levels completed from total levels",
                "Max Level Reached / Total Levels",
            ],
            [
                "GCA",
                "Game Completion Average",
                "The percentage of FTM learners acquired who have completed the game",
                "Learners wh completed 90% of the levels / Total learners",
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
        ],
        columns=["Acronym", "Name", "Definition", "Formula"],
    )
    expander.table(def_df)


def month_selector(placement="side", key=""):
    from calendar import month_abbr

    this_year = dt.datetime.now().year
    this_month = dt.datetime.now().month
    month_abbr = month_abbr[1:]

    if placement == "side":

        report_year = st.sidebar.selectbox(
            "Year", range(this_year, this_year - 4, -1), key=key
        )

        report_month_str = st.sidebar.radio(
            "Month",
            month_abbr,
            index=this_month - 1,
            horizontal=True,
            key=key + "x",
        )

    else:
        report_year = st.selectbox("Year", range(this_year, this_year - 4, -1), key=key)

        report_month_str = st.radio(
            "Month",
            month_abbr,
            index=this_month - 1,
            horizontal=True,
            key=key + "x",
        )
    report_month = month_abbr.index(report_month_str) + 1
    return report_month, report_year


def custom_date_selection_slider():
    # date_range = st.sidebar.date_input("Pick a date", (min_date, max_date))
    today = dt.datetime.now().date()
    last_year = dt.date(today.year, 1, 1) - relativedelta(years=1)

    date_range = st.sidebar.slider(
        label="Select Range:",
        min_value=dt.date(2021, 1, 1),
        value=(last_year, today),
        max_value=today,
    )


def custom_date_selection(placement="side", key=""):
    if placement == "side":
        date_range = st.sidebar.date_input("Pick a date", (min_date, max_date), key=key)
    else:
        date_range = st.date_input("Pick a date", (min_date, max_date), key=key)

    return date_range


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


def quarter_start(month):
    quarters = [1, 4, 7, 10]
    return (month - 1) // 3 * 3 + 1 if month in quarters else None


def year_selector(placement="side", key=""):
    this_year = dt.datetime.now().year
    if placement == "side":
        report_year = st.sidebar.radio(
            "Year", range(this_year, this_year - 4, -1), horizontal=True
        )
    else:
        report_year = st.radio(
            "Year", range(this_year, this_year - 4, -1), horizontal=True, key=key
        )

    return report_year


def ads_platform_selector():
    platform = st.sidebar.radio(
        label="Ads Platform",
        options=["Facebook", "Google", "Both"],
        horizontal=True,
        index=2,
    )
    return platform


def app_selector(placement="side"):

    if placement == "side":
        app = st.sidebar.radio(
            label="Application",
            options=["Unity", "CR", "Both"],
            horizontal=True,
            index=2,
        )
    else:
        app = st.radio(
            label="Application",
            options=["Unity", "CR", "Both"],
            horizontal=True,
            index=2,
        )
    return app


# Pass a unique key into the function in order to use this on multiple pages safely
def country_selector(placement="side", title="", key="key"):
    def update_country_session_state(key):
        if key in st.session_state:
            if st.session_state[key]:
                st.session_state.country = st.session_state[key]

    countries_list = users.get_country_list()
    countries_list.insert(0, "All")

    if placement == "side":
        country = st.sidebar.selectbox(
            label="Select a country",
            options=countries_list,
            index=0,
            key=key,
            on_change=update_country_session_state(key),
        )
    else:
        country = st.selectbox(
            label="Select a country",
            options=countries_list,
            index=0,
            key=key,
            on_change=update_country_session_state(key),
        )
    country_list = [country]
    return country_list


# This method uses the key parameter of the selectbox
# to automatically ad the selection to session state.
def language_selector(placement="side", key="lang_key"):
    # this is a callback for language_selector
    def update_language_session_state(key):
        if key in st.session_state:
            if st.session_state[key]:
                st.session_state.language = st.session_state[key]

    df = users.get_language_list()
    df.insert(0, "All")

    if placement == "side":
        language = st.sidebar.selectbox(
            label="Select a language",
            options=df,
            index=0,
            key=key,
            on_change=update_language_session_state(key),
        )
    else:
        language = st.selectbox(
            label="Select a language",
            options=df,
            index=0,
            key=key,
            on_change=update_language_session_state(key),
        )

    return language


# Pass a unique key into the function in order to use this on multiple pages safely
def multi_select_all(available_options, placement="side", title="", key="key"):
    available_options.insert(0, "All")

    # If a user switches to another page and comes back, selected options is dropped from session state
    # but max_selections still exists.  This has to do with how streamlit handles the key option in widgets
    # This will ensure All is selected when coming back to the page
    if key not in st.session_state:
        st.session_state[key] = ["All"]
    if "max_selections" not in st.session_state:
        st.session_state["max_selections"] = 1  # Enforce single selection
        st.session_state[key] = ["All"]  # Set default to "All"

    def options_select():  # Define options_select inside multi_select_all

        if key in st.session_state:
            if "All" in st.session_state[key]:
                st.session_state[key] = ["All"]  # Reset to "All" if deselected
                st.session_state["max_selections"] = 1  # Enforce single selection again
            else:
                st.session_state["max_selections"] = len(
                    available_options
                )  # Allow multiple selections

    if placement == "side":
        st.sidebar.multiselect(
            label=title,
            options=available_options,
            key=key,
            max_selections=st.session_state["max_selections"],
            on_change=options_select,  # Pass the function without calling it
            format_func=lambda x: "All" if x == "All" else f"{x}",
        )
        # Display options based on selection state
        if "All" in st.session_state[key]:
            st.sidebar.write("You selected all options.")
        else:
            st.sidebar.write(f"You selected {len(st.session_state[key])} options: ")
            st.sidebar.write(st.session_state[key])
    else:
        st.multiselect(
            label=title,
            options=available_options,
            key=key,
            max_selections=st.session_state["max_selections"],
            on_change=options_select,  # Pass the function without calling it
            format_func=lambda x: "All" if x == "All" else f"{x}",
        )

    return (
        available_options[1:]
        if "All" in st.session_state[key]
        else st.session_state[key]
    )  # Return full list if "All" is selected


@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df


def paginated_dataframe(df, keys, sort_col="campaign_name"):
    df.sort_values(by=sort_col)
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
            "Page Size", options=[500, 1000, 1500], key=keys[3], index=0
        )
    with bottom_menu[1]:
        total_pages = int(len(df) / batch_size) if int(len(df) / batch_size) > 0 else 1
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1, key=keys[4]
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")

    pages = split_frame(df, batch_size)
    pagination.dataframe(
        hide_index=True, data=pages[current_page - 1], use_container_width=True
    )


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


def stats_radio_selector():
    radio_markdown = """
    Learners Reached | Learners Acquired | Game Progress Percent | Game Completion Average 
    """.strip()
    option = st.radio(
        "Select a statistic",
        ("LR", "LA", "GPP", "GCA"),
        index=0,
        horizontal=True,
        help=radio_markdown,
    )
    return option


def app_version_selector(placement="side", key=""):
    cr_versions = st.session_state.cr_app_versions_list

    if placement == "side":
        version = st.sidebar.selectbox(
            label="App Version", options=cr_versions, key=key
        )
    else:
        version = st.selectbox(label="App Version", options=cr_versions, key=key)
    return version


def calendar_selector(placement="side", key=""):
    options = (
        "All time",
        "Select year",
        "Select month",
        "Select custom range",
    )

    with st.expander("Date"):

        if placement == "side":
            option = st.sidebar.radio(
                label="Select a date range", options=options, index=0, key=key + "1"
            )
        else:
            option = st.radio(
                label="Select a date range", options=options, index=0, key=key + "1"
            )

        if option == "Select year":
            selected_date = year_selector(placement=placement, key=key)
        elif option == "All time":
            selected_date = [min_date, max_date]
        elif option == "Select month":
            key = key + "x"
            selected_date = month_selector(placement, key=key)
        else:
            selected_date = custom_date_selection(placement, key=key)

    return selected_date, option
