import streamlit as st
import pandas as pd
import datetime as dt
from rich import print
from dateutil.relativedelta import relativedelta
import users
import calendar
import re
from streamlit_option_menu import option_menu

level_definitions = pd.DataFrame(
    [
        [
            "FO",
            "First Open",
            "The first time Curious Reader is opened from the play store",
       ],
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

    today = dt.datetime.now().date()
    last_year = dt.date(today.year, 1, 1) - relativedelta(years=1)

    date_range = st.sidebar.slider(
        label="Select Range:",
        min_value=dt.date(2021, 1, 1),
        value=(last_year, today),
        max_value=today,
    )


def custom_date_selection(placement="side", key=""):
    min_date = dt.datetime.now().date() - dt.timedelta(30)

    if placement == "side":
        date_range = st.sidebar.date_input(
            "Pick a date", [min_date, dt.date.today()], key=key
        )
    else:
        date_range = st.date_input("Pick a date", [min_date, dt.date.today()], key=key)

    return list(date_range)


def convert_date_to_range(selected_date, option):

    if option == "Select year":
        first = dt.date(selected_date, 1, 1)
        last = dt.date(selected_date, 12, 31)
        return [first, last]
    elif option == "All time":
        return [dt.datetime(2021, 1, 1).date(), dt.date.today()]
    elif option == "Select month":
        month = selected_date[0]
        year = selected_date[1]
        first = dt.date(year, month, 1)
        yearmonth = calendar.monthrange(year, month)
        last = dt.date(year, month, yearmonth[1])
        return [first, last]
    else: #already converted
        return selected_date


def quarter_start(month):
    quarters = [1, 4, 7, 10]
    return (month - 1) // 3 * 3 + 1 if month in quarters else None


def year_selector(placement="side", key=""):
    this_year = dt.datetime.now().year
    if placement == "side":
        report_year = st.sidebar.radio(
            "Year", range(this_year, this_year - 4, -1), horizontal=True, index=0, key=key + "_year"
        )
    else:
        report_year = st.radio(
            "Year", range(this_year, this_year - 4, -1), horizontal=True, key=key + "_year", index=0
        )

    # Make sure to return None if report_year is not properly selected
    return report_year if report_year is not None else None

def ads_platform_selector(placement="side"):
    label="Ads Platform"
    options=["Facebook", "Google", "Both"]
    horizontal=True
    index=2
    
    if placement == 'side':
        platform = st.sidebar.radio(
            label=label,
            options=options,
            horizontal=horizontal,
            index=index,
        )
    else:
        platform = st.radio(
            label=label,
            options=options,
            horizontal=horizontal,
            index=index,
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
def single_selector(selections, placement="side", title="", key="key"):
    # first time called for list, add 'All' option
    if selections[0] != "All":
        selections.insert(0, "All")

    if placement == "side":
        selection = st.sidebar.selectbox(
            label=title,
            options=selections,
            index=0,
            key=key,
        )

    else:
        selection = st.selectbox(
            label=title,
            options=selections,
            index=0,
            key=key,
        )

    selection_list = [selection]
    return selection_list


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
    df = df.sort_values(by=sort_col)
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

    selected_options = st.multiselect("Select versions:",cr_versions,key=key ,default='All')
    if 'All' in selected_options:
        selected_options = 'All'

    return selected_options


def calendar_selector(placement="side", key="", index=0):
    options = (
        "All time",
        "Select year",
        "Select month",
        "Select custom range",
        "Presets",
    )

    with st.expander("Date"):

        if placement == "side":
            option = st.sidebar.radio(
                label="Select a date range", options=options, index=index, key=key + "1"
            )
        else:
            option = st.radio(
                label="Select a date range", options=options, index=index, key=key + "1"
            )

        if option == "Select year":
            selected_date = year_selector(placement=placement, key=key)
        elif option == "All time":
            selected_date = [dt.datetime(2021, 1, 1).date(), dt.date.today()]
        elif option == "Select month":
            key = key + "x"
            selected_date = month_selector(placement, key=key)
        elif option == "Presets":
            selected_date = presets_selector(placement, key=key, index=3)
        else:
            selected_date = custom_date_selection(placement, key=key)

    return selected_date, option


presets = [
    "Last 7 days",
    "Last 14 days",
    "Last 30 days",
    "Last 90 days",
]


def presets_selector(placement="side", key="", index=1):
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

    if placement == "side":

        with st.sidebar:
            preset = option_menu(
                menu_title="",
                options=presets,
                icons=icons,
                orientation="horizontal",
                styles=styles,
                key=key,
                default_index=index,
            )
    else:
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


def compare_funnel_level_widget(placement="side", key=""):
    if placement == "side":
        toggle = st.sidebar.radio(
            options=[
                "Compare to Initial",
                "Compare to Previous",
            ],
            label="",
            horizontal=True,
            index=0,
            key=key,
            
        )
    else:
        toggle = st.radio(
            options=[
                "Compare to LR",
                "Compare to Previous",
            ],
            label="Compare",
            horizontal=False,
            index=0,
            key=key,
        )
    return toggle


def level_comparison_selector(placement="side"):
    col1, col2 = st.columns(2)
    levels = ["LR", "DC", "TS", "SL", "PC", "LA", "RA","GC"]
    upper_level = bottom_level = ""
    if placement == "side":
        bottom_level = st.sidebar.selectbox(
            label="Bottom level", options=levels, key="lcs-1", index=5
        )
        index_selected = levels.index(bottom_level)
        upper_levels = levels[:index_selected]
        upper_level = st.sidebar.selectbox(
            label="Upper level", options=upper_levels, key="lcs-2"
        )
    else:
        bottom_level = col1.selectbox(
            label="Bottom level", options=levels, key="lcs-3", index=5
        )
        index_selected = levels.index(bottom_level)
        upper_levels = levels[:index_selected]
        upper_level = col2.selectbox(
            label="Upper level", options=upper_levels, key="lcs-4"
        )
    return upper_level, bottom_level
