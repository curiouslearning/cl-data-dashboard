import streamlit as st
import pandas as pd
import datetime as dt
import calendar
from rich import print as rprint
import plost
import numpy as np


min_date = dt.datetime(2020,1,1).date()
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
                "LA",
                "Learner Acquisition",
                "The number of users that have completed at least one FTM level.",
                "COUNT(Learners)",
            ],
            [
                "GC",
                "Game Completion",
                "The average percentage of FTM levels completed per learner over a period of time (typically from the start of a campa",
                "AVG Max Level Reached / Total Levels",
            ],
            [
                "GCC",
                "Game Completion Cost",
                "The cost (USD) associated with one learner completing the average percentage of FTM levels (GC).",
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
    report_year = st.sidebar.selectbox("", range(this_year, this_year - 3, -1))

    return report_year

def month_selector():
    from calendar import month_abbr
    with st.sidebar.expander('Report month'):
        this_year = dt.datetime.now().year
        this_month = dt.datetime.now().month
        report_year = st.sidebar.selectbox("", range(this_year, this_year - 2, -1))
        month_abbr = month_abbr[1:]
        report_month_str = st.sidebar.radio("", month_abbr, index=this_month - 1, horizontal=True)
        report_month = month_abbr.index(report_month_str) + 1

    return report_month, report_year

        
def custom_date_selection():
    date_range = st.sidebar.date_input("Pick a date", (min_date, max_date))
    return (date_range)

def ads_platform_selector():
    platform = st.sidebar.radio(label="Ads Platform",
                                options=["Facebook","Google", "Both"],
                                horizontal=True,
                                index=2
    )
    return platform

def calendar_selector():
    option = st.sidebar.selectbox("Select a report date range",
        ("All time",
         "Select year",
         "Select month",
         "Select custom range"),
    index=None,
    placeholder="Select date range",
    )
    
    if (option == "Select year"):
        selected_date = year_selector()
    elif (option == "All time"):
        selected_date = [min_date,max_date]
    elif (option == "Select month"):
        selected_date = month_selector()
    else: 
        selected_date = custom_date_selection()
    return selected_date, option

def convert_date_to_range(selected_date,option):
    
    if (option == "Select year"):
        first = dt.date(selected_date, 1, 1)
        last = dt.date(selected_date, 12, 31)
        return [first,last]
    elif (option == "All time"):
        return [min_date,max_date]
    elif (option == "Select month"):
        month = selected_date[0]
        year = selected_date[1]
        first = dt.date(year, month, 1)
        yearmonth = calendar.monthrange(year, month)
        last = dt.date(year,month,yearmonth[1])
        return [first,last]
    else: 
        return selected_date
    
@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

def paginated_dataframe(df,keys):
     
    top_menu = st.columns(3)
    with top_menu[0]:
        sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=1, index=1,key=keys[0])
    if sort == "Yes":
        with top_menu[1]:
            sort_field = st.selectbox("Sort By", options=df.columns,key=keys[1])
        with top_menu[2]:
            sort_direction = st.radio(
                "Direction", options=["⬆️", "⬇️"], horizontal=True,key=keys[2]
            )
        df = df.sort_values(
            by=sort_field, ascending=sort_direction == "⬆️", ignore_index=True
        )

    
    pagination = st.container()
    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox("Page Size", options=[25, 50, 100],key=keys[3],index=1)
    with bottom_menu[1]:
        total_pages = (
            int(len(df) / batch_size) if int(len(df) / batch_size) > 0 else 1
        )
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1,key=keys[4]
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")

    pages = split_frame(df, batch_size)
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)
    
def top_campaigns_by_downloads_barchart(n):
    df_all = st.session_state.df_all
    df = df_all.filter(['campaign_name','mobile_app_install'], axis=1)    
    pivot_df = pd.pivot_table(
        df,
        index=['campaign_name'],        
        aggfunc={'mobile_app_install': np.sum})  

    df = pivot_df.sort_values(by=['mobile_app_install'],ascending=False)
    df.reset_index(inplace=True)
    df = df.rename(columns={"campaign_name": "Campaign", "mobile_app_install": "Installs"})
    df = df.head(n)
    plost.bar_chart(
        data=df,
        bar='Installs',
        value='Campaign',
        direction='vertical',
        use_container_width=True,    
        legend="bottom")
