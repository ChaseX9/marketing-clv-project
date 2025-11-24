import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ======================================
# CHARGEMENT DES DONNÉES
# ======================================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "online_retail_II_clean_scenario.csv")

    df = pd.read_csv(
        path,
        parse_dates=["InvoiceDate", "InvoiceMonth", "AcquisitionMonth"]
    )

    df["CustomerID"] = df["CustomerID"].astype(int)

    # AmountNet fallback
    if "AmountNet" not in df.columns:
        if "Amount" in df.columns:
            df["AmountNet"] = df["Amount"]
        else:
            df["AmountNet"] = df["Quantity"] * df["UnitPrice"]

    # Détection des retours
    if "IsReturn" not in df.columns and "InvoiceNo" in df.columns:
        df["IsReturn"] = df["InvoiceNo"].astype(str).str.startswith("C")

    return df


# ======================================
# RFM
# ======================================
def compute_rfm(df):
    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    return df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("AmountNet", "sum"),
    )


# ======================================
# NORTH STAR
# ======================================
def compute_north_star(df):
    df = df.copy()
    first_purchase = df.groupby("CustomerID")["InvoiceDate"].min().rename("FirstPurchase")
    df = df.merge(first_purchase, on="CustomerID", how="left")

    df_90 = df[df["InvoiceDate"] <= df["FirstPurchase"] + pd.Timedelta(days=90)]
    total_rev = df_90["AmountNet"].sum()
    n_clients = df_90["CustomerID"].nunique()

    return total_rev / n_clients if n_clients > 0 else 0.0


# ======================================
# KPIS GLOBAUX
# ======================================
def compute_kpis(df):
    df = df.copy()
    kpis = {}

    # Clients actifs
    kpis["active_clients"] = df["CustomerID"].nunique()

    # CLV baseline
    total_rev = df["AmountNet"].sum()
    kpis["clv_baseline"] = total_rev / kpis["active_clients"]

    # RFM
    rfm = compute_rfm(df)
    kpis["rfm_count"] = len(rfm)

    # CA moyen par âge de cohorte
    inv = df["InvoiceMonth"].dt.to_period("M")
    acq = df["AcquisitionMonth"].dt.to_period("M")
    df["CohortAge"] = (inv - acq).apply(lambda x: x.n)
    df = df[df["CohortAge"] >= 0]

    rev_by_age = df.groupby("CohortAge")["AmountNet"].sum()
    kpis["avg_rev_per_age"] = rev_by_age.mean() if not rev_by_age.empty else 0.0

    # North Star
    kpis["north_star"] = compute_north_star(df)

    return kpis


# ======================================
# PAGE OVERVIEW
# ======================================
def show():
    """Affiche la page Overview complète."""
    st.header("📊 Overview – KPIs Globaux")

    # Charger données
    df = load_data()

    # KPIs
    kpis = compute_kpis(df)

    # Période globale
    period_str = f"{df['InvoiceDate'].min().strftime('%d/%m/%Y')} → {df['InvoiceDate'].max().strftime('%d/%m/%Y')}"
    st.markdown(f"**Période analysée :** {period_str}")

    st.markdown("---")
    st.subheader("🔹 KPIs Globaux")

    # Ligne 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Clients actifs", f"{kpis['active_clients']:,}".replace(",", " "))
    c2.metric("CA / âge de cohorte (€)", f"{kpis['avg_rev_per_age']:,.2f}".replace(",", " "))
    c3.metric("CLV baseline (€)", f"{kpis['clv_baseline']:,.2f}".replace(",", " "))

    # Ligne 2
    c4, c5 = st.columns(2)
    c4.metric("Taille RFM (clients profilés)", f"{kpis['rfm_count']:,}".replace(",", " "))
    c5.metric("North Star (CA 90j / client)", f"{kpis['north_star']:,.2f}".replace(",", " "))

    # ==========================
    # AIDE INTÉGRÉE
    # ==========================
    with st.expander("ℹ️ Aide intégrée — définitions & exemples"):
        st.markdown(
            """
            ### 🧩 Définitions des KPIs

            **Clients actifs**  
            Nombre de clients uniques ayant réalisé au moins une transaction.

            **CA / âge de cohorte (€)**  
            Moyenne du CA total généré par âge de cohorte (H0, H1, H2…).

            **CLV baseline (€)**  
            CA total / nombre de clients actifs.

            **RFM**  
            Recency (jours depuis dernier achat)  
            Frequency (nombre de factures)  
            Monetary (montant total dépensé)

            **North Star Metric**  
            CA généré par client dans les 90 jours suivant l'acquisition.
            """
        )

    # ==========================
    # CA MENSUEL GLOBAL — PLOTLY
    # ==========================
    st.markdown("---")
    st.subheader("📈 CA mensuel global")

    monthly = df.groupby(df["InvoiceMonth"].dt.to_period("M"))["AmountNet"].sum()
    monthly.index = monthly.index.to_timestamp()

    fig = px.line(
        x=monthly.index,
        y=monthly.values,
        labels={"x": "Mois", "y": "CA (€)"},
        title="CA mensuel global"
    )

    fig.update_layout(
        template="plotly_dark",
        showlegend=False,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)