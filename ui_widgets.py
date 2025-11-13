import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
import calendar
import re
from streamlit_option_menu import option_menu

level_definitions = pd.DataFrame(
    [
        [
            "LR",
            "Learner Reached",
            "The number of users that downloaded and opened the app",
       ],
        [
            "PC",
            "Puzzle Complete / Drgged a Stone",
            "The number of users that have completed at least one puzzle",
        ],
        [
            "LA",
            "Learner Acquisition",
            "The number of users that have completed at least one FTM level.",
        ],        [
            "RA",
            "Reader Acquired",
            "The number of users that have completed at least 25 levels",
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
            "LAC",
            "Learner Acquisition Cost",
            "The cost (USD) of acquiring one learner.",
            "Total Spend / LA",
        ],
    ],
    columns=["Acronym", "Name", "Definition", "Formula"],
)
level_percent_definitions = pd.DataFrame(
    [
        [
            "DC over LR",
            "Downloads Completed divided by Learners Reached",
        ],
        [
            "TS over LR",
            "Tapped Start divided by Learners Reached",
        ],
        [
            "SL over LR",
            "Selected Level divided by Learners Reached",
        ],
        [
            "PC over LR",
            "Puzzle Completed divided by Learners Reached",
        ],
        [
            "LA over LR",
            "Learner Acquired (Level completed) divided by Learners Reached",
        ],
        [
            "GC over LR",
            "Game Complted divided by Learners Reached",
        ],
    ],
    columns=["Name", "Definition"],
)

data_notes = pd.DataFrame(
    [
        [
            "Curious Reader LR",
            "The first event where we have an associated language in Curious Reader is the app_launch event so this is the chosen event for LR in Curious Reader",
        ],
        [
            "Curious Reader LR",
            "Individual users may have multiple languages or countries so we select their entry with the furthest progress and eliminate their other entries",
        ],
    ],
    columns=["Note", "Description"],
)

def display_definitions_table(title,def_df):
    expander = st.expander(title)
    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    expander.table(def_df)


def month_selector(key=""):
    from calendar import month_abbr

    this_year = dt.datetime.now().year
    this_month = dt.datetime.now().month
    month_abbr = month_abbr[1:]

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


def slider_callback():
    # Ensure the session state reflects the slider value
    left_value, right_value = st.session_state.slider_value

    # Validate and correct if the right value exceeds max_date
    if right_value > st.session_state.max_date:
        st.session_state.slider_date = (left_value, st.session_state.max_date)
        st.session_state.slider_value = st.session_state.slider_date  # Update slider_value to reflect change
        st.info ("You can't select a date inside the buffer zone. Resetting to end of buffer zone.", icon="⚠️")
    else:
        st.session_state.slider_date = (left_value, right_value)


def custom_date_selection(key=""):
    min_date = dt.datetime.now().date() - dt.timedelta(30)

    date_range = st.date_input("Pick a date", [min_date, dt.date.today()], key=key)

    return list(date_range)


def convert_date_to_range(selected_date, option, end_date=None):
    today = dt.datetime.today().date()
    
    if option == "Select year":
        first = dt.date(selected_date, 1, 1)
        last = dt.date(selected_date, 12, 31)
    elif option == "All time":
        first = dt.date(2021, 1, 1)
        last = today
    elif option == "Select month":
        month, year = selected_date
        first = dt.date(year, month, 1)
        last = dt.date(year, month, calendar.monthrange(year, month)[1])
    else:  # already converted
        return selected_date

    # Ensure last date does not exceed today
    last = min(last, today if end_date is None else min(end_date, today))

    return [first, last]

def quarter_start(month):
    quarters = [1, 4, 7, 10]
    return (month - 1) // 3 * 3 + 1 if month in quarters else None

def year_selector(key=""):
    this_year = dt.datetime.now().year

    report_year = st.radio(
        "Year", range(this_year, 2020, -1), horizontal=True, key=key + "_year", index=0
    )

    # Make sure to return None if report_year is not properly selected
    return report_year if report_year is not None else None


def colorize_multiselect_options() -> None:
    colors = [
        "#394a51",
        "#7fa99b",
        "#fbf2d5",
        "#fdc57b",
    ]

    rules = ""
    n_colors = len(colors)

    for i, color in enumerate(colors):
        rules += f""".stMultiSelect div[data-baseweb="select"] span[data-baseweb="tag"]:nth-child({n_colors}n+{i}){{background-color: {color};}}"""

    st.markdown(f"<style>{rules}</style>", unsafe_allow_html=True)


# Restricts selection to a single country
def single_selector(selections,  title="", key="key", include_All=True,index=0):
    options = list(selections)  # Defensive copy

    if include_All:
        if "All" not in options:
            options = ["All"] + [s for s in options if s != "All"]
    else:
        options = [s for s in options if s != "All"]

    selection = st.selectbox(
        index=index,
        label=title,
        options=options,
        key=key,
    )

    return [selection]


# Pass a unique key into the function in order to use this on multiple pages safel

def multi_select_all(available_options,  title="", key="key"):
    available_options.insert(0, "All")

    # Ensure each instance has its own session state keys
    if key not in st.session_state:
        st.session_state[key] = ["All"]
    if f"{key}_max_selections" not in st.session_state:
        st.session_state[f"{key}_max_selections"] = 1  # Unique max selection per widget
        st.session_state[key] = ["All"]  # Set default to "All"

    def options_select():  # Define options_select inside multi_select_all
        if key in st.session_state:
            if "All" in st.session_state[key]:
                st.session_state[key] = ["All"]  # Reset to "All" if deselected
                st.session_state[f"{key}_max_selections"] = 1  # Unique max selection
            else:
                st.session_state[f"{key}_max_selections"] = len(available_options)  # Allow multiple selections


    st.multiselect(
        label=title,
        options=available_options,
        key=key,
        max_selections=st.session_state[f"{key}_max_selections"],  # Unique max selection key
        on_change=options_select,  
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


def stats_radio_selector():
    radio_markdown = """
    Learners Reached | Learners Acquired | Reader Acquired | Game Completed 
    """.strip()
    option = st.radio(
        "Select a statistic",
        ("LR", "LA", "RA", "GC"),
        index=0,
        horizontal=True,
        help=radio_markdown,
    )
    return option


def calendar_selector(key="", index=0, title="Date"):
    options = (
        "All time",
        "Select year",
        "Select month",
        "Select custom range",
        "Presets",
    )

    option = st.radio(
        label="Select a date range", options=options, index=index, key=key + "1"
    )

    if option == "Select year":
        selected_date = year_selector(key=key)
    elif option == "All time":
        selected_date = [dt.datetime(2021, 1, 1).date(), dt.date.today()]
    elif option == "Select month":
        key = key + "x"
        selected_date = month_selector(key=key)
    elif option == "Presets":
        selected_date = presets_selector( key=key, index=3)
    else:
        selected_date = custom_date_selection(key=key)

    return selected_date, option


presets = [
    "Last 7 days",
    "Last 14 days",
    "Last 30 days",
    "Last 90 days",
]


def presets_selector(key="", index=1):
    dates = []
    icons = ["peace", "yin-yang", "sun", "heart"]
    styles = {
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "15px"},
        "nav-link": {
            "font-size": "12px",
            "text-align": "left",
            "margin": "2px",
            "--hover-color": "#eee",
        },
        "nav-link-selected": {"background-color": "#394a51"},
    }
    preset = option_menu(
        menu_title="",
        options=presets,
        icons=["peace", "yin-yang", "sun", "heart"],
        orientation="horizontal",
        styles=styles,
        key=key,
        default_index=index,
    )
    if preset:
        dates = calculate_preset_dates(preset)

    return dates


def calculate_preset_dates(preset):

    pattern = r"\d+"
    numeric_part = re.findall(pattern, preset)

    # Converting the extracted numeric part to an integer
    numeric_part = int(
        numeric_part[0]
    )  # numeric_part[0] contains the first (and only) element of the list

    start_date = dt.datetime.now().date() - dt.timedelta(numeric_part)
    end_date = dt.datetime.now().date()

    return [start_date, end_date]


@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")

def get_apps():
    distinct_apps = sorted(st.session_state["df_cr_users"]["app"].dropna().unique())
    distinct_apps.append("Unity")
    distinct_apps.sort()
    return distinct_apps

def is_compact(apps):
    # Handles string or list
    if isinstance(apps, list):
        return any(
            (
                a == "Unity"
                or a == "All"
                or (isinstance(a, str) and "standalone" in a.lower())
            )
            for a in apps
            if a
        )
    else:
        a = apps
        return (
            a == "Unity"
            or a == "All"
            or (isinstance(a, str) and "standalone" in a.lower())
        )
