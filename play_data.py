import streamlit as st
import pandas as pd
from rich import print as print


@st.cache_data(show_spinner="Fetching Google Play Data", ttl="1d")
def get_play_installs():
    bq_client = st.session_state.bq_client
    sql_query = f"""
        SELECT
            Date,
            Package_name,
            Country,
            Daily_Device_Installs,
        FROM dataexploration-193817.play_data.p_Installs_country_play
        WHERE
            Package_name =  'org.curiouslearning.container' OR
            Package_name LIKE '%feedthemonster%'
      
    """
    rows_raw = bq_client.query(sql_query)
    rows = [dict(row) for row in rows_raw]

    df = pd.DataFrame(rows)
    return df
