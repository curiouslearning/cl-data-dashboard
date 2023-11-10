import streamlit as st
import pandas as pd
import settings 

logger = settings.init_logging()
secrets = settings.get_secrets()


## UI ##
st.title("Curious Learning Dashboard")

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
