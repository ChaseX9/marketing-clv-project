import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io


# === Chargement des données ===
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "online_retail_II_clean_scenario.csv")
    df = pd.read_csv(path, parse_dates=['InvoiceDate', 'InvoiceMonth', 'AcquisitionMonth'])
    return df



def show():

    st.title("📊 Analyse des Cohortes")

    # ==============================
    # LOAD DATA
    # ==============================
    df = load_data()

    # === Mapping Pays → Continent ===
    continent_map = {
        "United Kingdom": "Europe", "Germany": "Europe", "France": "Europe", "Spain": "Europe",
        "Portugal": "Europe", "Italy": "Europe", "Belgium": "Europe",
        "Australia": "Oceania", "New Zealand": "Oceania",
        "USA": "America", "Canada": "America",
        "Japan": "Asia", "China": "Asia", "Singapore": "Asia"
    }

    df["Continent"] = df["Country"].map(continent_map).fillna("Other")

    # ==============================
    # FILTRES SIDEBAR
    # ==============================
    st.sidebar.header("Filtres")

    # Géographie
    geo_filter = st.sidebar.radio("Filtrer par :", ["Tous", "Continent", "Pays"])

    if geo_filter == "Continent":
        continent_choice = st.sidebar.selectbox("Choisir un continent", sorted(df["Continent"].unique()))
        df = df[df["Continent"] == continent_choice]

    elif geo_filter == "Pays":
        pays_choice = st.sidebar.multiselect("Choisir un ou plusieurs pays", sorted(df["Country"].unique()))
        if pays_choice:
            df = df[df["Country"].isin(pays_choice)]

    # Filtre temporel
    st.sidebar.subheader("Filtre temporel")
    min_date = df["AcquisitionMonth"].min()
    max_date = df["AcquisitionMonth"].max()

    date_range = st.sidebar.date_input(
        "Sélectionner une période d'acquisition",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df["AcquisitionMonth"] >= pd.to_datetime(start_date)) &
                (df["AcquisitionMonth"] <= pd.to_datetime(end_date))]

    # Filtre Cohortes
    st.sidebar.subheader("Filtre par cohortes")
    cohortes = sorted(df["AcquisitionMonth"].dt.strftime("%Y-%m").unique())

    selected_cohortes = st.sidebar.multiselect(
        "Sélectionner des cohortes",
        options=cohortes,
        default=cohortes
    )

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Tout sélectionner"):
        selected_cohortes = cohortes
    if col2.button("Tout désélectionner"):
        selected_cohortes = []

    df = df[df["AcquisitionMonth"].dt.strftime("%Y-%m").isin(selected_cohortes)]

    # ==============================
    # CALCUL DES COHORTES
    # ==============================
    df["CohortAge"] = (
        (df["InvoiceMonth"].dt.year - df["AcquisitionMonth"].dt.year) * 12 +
        (df["InvoiceMonth"].dt.month - df["AcquisitionMonth"].dt.month)
    )

    cohort_data = df.groupby(["AcquisitionMonth", "CohortAge"])["CustomerID"].nunique().reset_index()

    cohort_sizes = cohort_data[cohort_data["CohortAge"] == 0][["AcquisitionMonth", "CustomerID"]]\
                    .rename(columns={"CustomerID": "CohortSize"})

    cohort_data = cohort_data.merge(cohort_sizes, on="AcquisitionMonth")
    cohort_data["RetentionRate"] = cohort_data["CustomerID"] / cohort_data["CohortSize"]

    # ==============================
    # HEATMAP RETENTION
    # ==============================
    retention_matrix = cohort_data.pivot(
        index="AcquisitionMonth", columns="CohortAge", values="RetentionRate"
    )

    fig_heatmap = px.imshow(
        retention_matrix,
        labels=dict(x="Âge de cohorte (mois)", y="Mois d'acquisition", color="Taux de rétention"),
        x=retention_matrix.columns,
        y=retention_matrix.index,
        color_continuous_scale="Blues"
    )
    fig_heatmap.update_layout(title="Heatmap de rétention par cohortes")

    st.plotly_chart(fig_heatmap, use_container_width=True)

    with st.expander("ℹ️ Aide : Heatmap de rétention"):
        st.markdown("""
        **Définition :** La heatmap montre le **taux de rétention** par âge de cohorte.  
        - **Ligne = cohorte d’acquisition**  
        - **Colonne = âge en mois (M+1, M+2, ...)**

        *Exemple : Si M+3 = 40 %, alors 40 % des clients sont encore actifs 3 mois après.*
        """)

    # ==============================
    # COURBE CA PAR ÂGE DE COHORTE
    # ==============================
    revenue_data = df.groupby("CohortAge")["AmountNet"].sum().reset_index()

    fig_revenue = px.line(
        revenue_data, x="CohortAge", y="AmountNet",
        labels={"CohortAge": "Âge de cohorte (mois)", "AmountNet": "CA net"},
        title="Dynamique du CA par âge de cohorte"
    )

    st.plotly_chart(fig_revenue, use_container_width=True)

    with st.expander("ℹ️ Aide : Courbe CA par âge"):
        st.markdown("""
        Montre combien les cohortes génèrent de CA selon leur âge.  
        *Exemple : à M+6 = 5 000 €, cela signifie que les cohortes génèrent 5k€ au 6ᵉ mois après acquisition.*
        """)

    # ==============================
    # FOCUS COHORTE
    # ==============================
    st.subheader("Focus sur une cohorte")

    cohorte_select = st.selectbox("Choisir une cohorte", options=selected_cohortes)

    focus_data = df[df["AcquisitionMonth"].dt.strftime("%Y-%m") == cohorte_select]
    focus_revenue = focus_data.groupby("CohortAge")["AmountNet"].sum().reset_index()

    fig_focus = px.bar(
        focus_revenue, x="CohortAge", y="AmountNet",
        labels={"CohortAge": "Âge (mois)", "AmountNet": "CA net"},
        title=f"CA par âge pour la cohorte {cohorte_select}"
    )

    st.plotly_chart(fig_focus, use_container_width=True)

    with st.expander("ℹ️ Aide : Focus cohorte"):
        st.markdown("""
        Analyse le comportement d’une cohorte spécifique.  
        *Exemple : Janvier 2010 → M+1 = 2000 €, M+2 = 1500 € → baisse progressive.*
        """)

    # ==============================
    # INDICATEURS CLÉS
    # ==============================
    st.subheader("📈 Indicateurs clés")

    clv_moyenne = df.groupby("CustomerID")["AmountNet"].sum().mean()

    df["DaysSinceAcquisition"] = (df["InvoiceDate"] - df["AcquisitionMonth"]).dt.days
    ca_90 = df[df["DaysSinceAcquisition"] <= 90].groupby("CustomerID")["AmountNet"].sum().mean()

    retention_m3 = cohort_data[cohort_data["CohortAge"] == 3]["RetentionRate"].mean() * 100

    clv_empirique = df.groupby("CustomerID")["AmountNet"].sum().mean()

    marge = 10
    r = 0.8
    d = 0.1
    clv_formula = (marge * r) / (1 + d - r)

    st.metric("CLV moyenne", f"{clv_moyenne:.2f} €")
    st.metric("CA à 90 jours", f"{ca_90:.2f} €")
    st.metric("Rétention M+3", f"{retention_m3:.1f} %")
    st.metric("CLV empirique", f"{clv_empirique:.2f} €")
    st.metric("CLV (formule)", f"{clv_formula:.2f} €")

    with st.expander("ℹ️ Aide : Indicateurs clés"):
        st.markdown("""
        Explications des métriques principales :
        - **CLV moyenne** : valeur générée par client.
        - **CA à 90 jours** : revenu moyen après acquisition.
        - **Rétention M+3** : % de clients actifs au 3ᵉ mois.
        - **CLV formule fermée** : basée sur marge, rétention, actualisation.
        """)

    # ==============================
    # TABLEAU RFM
    # ==============================
    rfm = df.groupby("CustomerID").agg({
        "InvoiceDate": lambda x: (df["InvoiceDate"].max() - x.max()).days,
        "InvoiceNo": "count",
        "AmountNet": "sum"
    }).rename(columns={"InvoiceDate": "Recency", "InvoiceNo": "Frequency", "AmountNet": "Monetary"})

    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1])
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1,2,3,4,5])
    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str) +
        rfm["F_Score"].astype(str) +
        rfm["M_Score"].astype(str)
    )

    st.write("Tableau RFM", rfm.head())

    with st.expander("ℹ️ Aide : Tableau RFM"):
        st.markdown("""
        - **Recency** : jours depuis la dernière commande  
        - **Frequency** : nombre de commandes  
        - **Monetary** : montant total dépensé  
        - **RFM Score** : profil client (ex : 555 = Champion)
        """)

    # ==============================
    # EXPORTS
    # ==============================
    csv_df = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger données filtrées (CSV)", csv_df, "cohortes_filtrees.csv")

    csv_rfm = rfm.to_csv(index=True).encode('utf-8')
    st.download_button("📥 Télécharger tableau RFM (CSV)", csv_rfm, "rfm_table.csv")

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    st.download_button(
        "📥 Télécharger données filtrées (Excel)",
        excel_buffer,
        "cohortes_filtrees.xlsx",
    )

    rfm_buffer = io.BytesIO()
    rfm.to_excel(rfm_buffer, index=True)
    rfm_buffer.seek(0)

    st.download_button(
        "📥 Télécharger tableau RFM (Excel)",
        rfm_buffer,
        "rfm_table.xlsx",
    )