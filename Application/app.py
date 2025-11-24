import streamlit as st
from utils import render_header
from pages.overview import show as show_overview
from pages.scenario import show as show_scenarios
from pages.cohortes import show as show_cohortes
from pages.segments import show as show_segments

# Header commun
render_header()

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Overview", "Cohortes", "Segments", "Scénarios", "Export"]
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
elif page == "Export":
    st.header("Export")
    st.write("Ici on pourra exporter les données filtrées et les graphiques.")
