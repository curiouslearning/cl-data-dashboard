import streamlit as st
from st_pages import add_page_title, get_nav_from_toml
import sys

# ---------------------------------------------------------
# 🌐 PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(layout="wide")

nav = get_nav_from_toml(".streamlit/pages.toml")
pg = st.navigation(nav)
add_page_title(pg)

# ---------------------------------------------------------
# ▶️ RUN THE CURRENT PAGE
# ---------------------------------------------------------
pg.run()

# ---------------------------------------------------------
# 🦶 FOOTER
# ---------------------------------------------------------
footer_html = f"""
<style>
footer {{
    position: fixed;
    bottom: 0;
    width: 100%;
    text-align: center;
    padding: 5px;
    background-color: #f0f2f6;
    color: #555;
    font-size: 0.9em;
}}
</style>

<footer>
Python {sys.version.split()[0]} | Streamlit {st.__version__}
</footer>
"""

st.markdown(footer_html, unsafe_allow_html=True)