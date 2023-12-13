import streamlit as st
import pandas as pd
from rich import print as print


@st.cache_data(show_spinner="Fetching Play Event Data", ttl="1d")
def get_play_event_data(_bq_client):

    sql_query = f"""
            SELECT 
            event_name,
            parse_date('%Y%m%d',event_date) as day,
            app_id,
            country
            FROM dataexploration-193817.play_data.events
            WHERE
            parse_date('%Y%m%d',event_date) BETWEEN '2020-01-01' AND CURRENT_DATE()  ;
             """

    rows_raw = _bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    if (len(rows) == 0):
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    return(df)

