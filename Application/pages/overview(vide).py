import os
import sys
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ===========================
# Import render_header
# ===========================
BASE_DIR_APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR_APP not in sys.path:
    sys.path.append(BASE_DIR_APP)

try:
    from utils import render_header
except ImportError:
    from Application.utils import render_header


# ===========================
# 1️⃣ Chargement des données
# ===========================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "online_retail_II_clean_scenario.csv")

    df = pd.read_csv(
        path,
        parse_dates=["InvoiceDate", "InvoiceMonth", "AcquisitionMonth"],
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


# ===========================
# 2️⃣ RFM
# ===========================
def compute_rfm(df):
    df = df.copy()
    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("AmountNet", "sum"),
    )
    return rfm


# ===========================
# 3️⃣ North Star (CA 90 jours)
# ===========================
def compute_north_star(df):
    df = df.copy()
    first_purchase = df.groupby("CustomerID")["InvoiceDate"].min().rename("FirstPurchase")
    df = df.merge(first_purchase, on="CustomerID", how="left")

    df_90 = df[df["InvoiceDate"] <= df["FirstPurchase"] + pd.Timedelta(days=90)]
    total_rev = df_90["AmountNet"].sum()
    n_clients = df_90["CustomerID"].nunique()

    return total_rev / n_clients if n_clients > 0 else 0.0


# ===========================
# 4️⃣ KPIs globaux
# ===========================
def compute_kpis(df):
    kpis = {}

    # Clients actifs
    kpis["active_clients"] = df["CustomerID"].nunique()

    # CA total et CLV baseline
    total_rev = df["AmountNet"].sum()
    kpis["clv_baseline"] = total_rev / kpis["active_clients"]

    # RFM
    rfm = compute_rfm(df)
    kpis["rfm_count"] = len(rfm)

    # CA / âge de cohorte (moyenne)
    inv = df["InvoiceMonth"].dt.to_period("M")
    acq = df["AcquisitionMonth"].dt.to_period("M")

    df["CohortAge"] = (inv - acq).apply(lambda x: x.n)
    df = df[df["CohortAge"] >= 0]

    rev_by_age = df.groupby("CohortAge")["AmountNet"].sum()

    kpis["avg_rev_per_age"] = rev_by_age.mean() if not rev_by_age.empty else 0.0

    # North Star
    kpis["north_star"] = compute_north_star(df)

    return kpis


# ===========================
# 5️⃣ Page Overview
# ===========================
def main():
    df = load_data()

    # Header global
    render_header(
        start_date=df["InvoiceDate"].min().strftime("%d/%m/%Y"),
        end_date=df["InvoiceDate"].max().strftime("%d/%m/%Y")
    )

    st.subheader("📊 Overview - Synthèse globale")

    kpis = compute_kpis(df)

    st.markdown("---")
    st.subheader("🔹 KPIs Globaux")

    col1, col2, col3 = st.columns(3)

    col1.metric("Clients actifs", f"{kpis['active_clients']:,}".replace(",", " "))
    col2.metric("CA / âge de cohorte (€)", f"{kpis['avg_rev_per_age']:,.2f}".replace(",", " "))
    col3.metric("CLV baseline (€)", f"{kpis['clv_baseline']:,.2f}".replace(",", " "))

    col4, col5 = st.columns(2)
    col4.metric("Taille RFM (clients profilés)", f"{kpis['rfm_count']:,}".replace(",", " "))
    col5.metric("North Star (CA 90j / client)", f"{kpis['north_star']:,.2f}".replace(",", " "))

    # -------------------------
    # Graphique CA mensuel global
    # -------------------------
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


if __name__ == "__main__":
    main()