import streamlit as st

def render_header(start_date="01/12/2009", end_date="09/12/2011"):
    st.markdown(
        f"""
        <div style="background-color:#1f77b4;padding:15px;border-radius:5px">
            <h1 style="color:white;margin-bottom:0">Marketing Dashboard</h1>
            <p style="color:white;margin-top:0;font-size:16px">
                Analyse cohortes, segmentation RFM et CLV | Période : {start_date} - {end_date}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )