import streamlit as st


st.set_page_config(
    page_title="Marketing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils import render_header
from pages.overview import show as show_overview
from pages.scenario import show as show_scenarios
from pages.cohortes import show as show_cohortes
from pages.segments import show as show_segments

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Header commun
render_header()

# Sidebar navigation
st.sidebar.markdown("## 📊 Navigation")
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Overview", "Cohortes", "Segments", "Scénarios"]
)

# Contenu placeholder pour tester
if page == "Overview":
    st.header("Overview (KPIs)")
    show_overview()
elif page == "Cohortes":
    st.header("Cohortes")
    show_cohortes()
elif page == "Segments":
    st.header("Segments RFM")
    show_segments()
elif page == "Scénarios":
    st.header("Scénarios")
    show_scenarios()

