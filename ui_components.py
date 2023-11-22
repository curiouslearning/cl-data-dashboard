import streamlit as st
import pandas as pd
import datetime as dt
import calendar

min_date = dt.datetime(2020,1,1)
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
    st.sidebar.text(f'{report_year}')
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
    st.sidebar.text(f'{report_year} {report_month_str}')
    return report_month, report_year

        
def custom_date_selection():
    date_range = st.sidebar.date_input("Pick a date", (min_date, max_date))
    return (date_range)

def calendar_selector():
    option = st.sidebar.selectbox("Select a report date range",
        ("All time",
         "Select year",
         "Select month",
         "Select custom range"),
    index=1,
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
    
