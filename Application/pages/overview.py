import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

    if "AmountNet" not in df.columns:
        if "Amount" in df.columns:
            df["AmountNet"] = df["Amount"]
        else:
            df["AmountNet"] = df["Quantity"] * df["UnitPrice"]

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

    # Charger les données
    df = load_data()

    # Calculer les KPIs
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
            Nombre de clients uniques ayant réalisé au moins une transaction dans toute la période.  
            *Exemple : Si 4 372 clients différents ont acheté au moins une fois → Clients actifs = 4 372.*

            ---

            **CA / âge de cohorte (€)**  
            Pour chaque *CohortAge* (H0, H1, H2...), on calcule le CA total et on en fait la moyenne.  
            *Exemple : Si H0 = 120k€, H1 = 90k€, H2 = 110k€ alors CA moyen par âge = (120+90+110)/3 = 106,6k€.*

            ---

            **CLV baseline (€)**  
            CA total de la période ÷ nombre de clients actifs.  
            *Exemple : 4 000 000€ de CA et 4 000 clients actifs → CLV baseline = 1 000€.*

            ---

            **RFM (Recency – Frequency – Monetary)**  
            - *Recency* : nombre de jours depuis le dernier achat  
            - *Frequency* : nombre de factures uniques  
            - *Monetary* : somme totale dépensée  
            *Exemple : un client a acheté 5 fois pour 450€, dernier achat il y a 12 jours → R=12, F=5, M=450.*

            ---

            **North Star Metric : CA 90 jours / client**  
            CA généré dans les 90 jours suivant la première transaction, en moyenne par client.  
            *Exemple : 80 000€ générés dans les 90 premiers jours par 1 000 clients → North Star = 80€.*

            ---
            """
        )

    # ==========================
    # CA MENSUEL GLOBAL
    # ==========================
    st.markdown("---")
    st.subheader("📈 CA mensuel global")

    monthly = df.groupby(df["InvoiceMonth"].dt.to_period("M"))["AmountNet"].sum()
    monthly.index = monthly.index.to_timestamp()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(monthly.index, monthly.values, marker="o")
    ax.set_title("CA mensuel global")
    ax.set_ylabel("CA (€)")
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)

    st.pyplot(fig)