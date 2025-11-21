import streamlit as st
from utils import render_header
from pages.overview import show as show_overview
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
    st.write("Ici on affichera la heatmap de rétention et les courbes CA par âge de cohorte.")
elif page == "Segments":
    st.header("Segments RFM")
    st.write("Ici on affichera la table RFM et la priorisation des segments.")
elif page == "Scénarios":
    st.header("Scénarios")
    st.write("Ici on affichera les sliders pour simuler l’impact sur CLV, CA et marge.")
elif page == "Export":
    st.header("Export")
    st.write("Ici on pourra exporter les données filtrées et les graphiques.")
