# app/scenarios.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ===========================
# Charger les données clean
# ===========================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "online_retail_II_clean_scenario.csv")
    df = pd.read_csv(path, parse_dates=['InvoiceDate', 'InvoiceMonth', 'AcquisitionMonth'])
    df['CustomerID'] = df['CustomerID'].astype(int)
    if 'AmountNet' not in df.columns:
        df['AmountNet'] = df['Amount']
    return df


def show():
    df = load_data()

    st.title("📊 Scénarios - Simulation Marketing")
    st.write("")
    st.markdown(
        """
        Bienvenue sur la page **Scénarios** ! 🎯  
        Utilisez les **sliders** situés dans la **sidebar** pour **configurer votre scénario** et visualiser en temps réel l'impact sur les **KPI** tels que le **CLV**, le **CA total** et la **rétention transactionnelle**.  

        Ajustez les paramètres comme la **variation de marge**, la **remise moyenne** et la **variation de rétention** pour observer comment ils influencent vos résultats.
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    # ===========================
    # Sidebar : paramètres de simulation
    # ===========================
    st.sidebar.header("⚙️ Paramètres de simulation")
    marge_pct = st.sidebar.slider("Variation marge (%)", -50, 50, 0, 1)
    discount_pct = st.sidebar.slider("Remise moyenne (%)", 0, 50, 0, 1)
    retention_pct = st.sidebar.slider("Variation rétention (%)", -50, 20, 0, 1)

    cohorte_selection = st.sidebar.selectbox(
        "Cohorte cible",
        ["Toutes"] + sorted(df['AcquisitionMonth'].dt.to_period('M').astype(str).unique().tolist())
    )

    # ===========================
    # Filtrage cohorte
    # ===========================
    df_sim = df.copy()
    if cohorte_selection != "Toutes":
        df_sim = df_sim[df_sim['AcquisitionMonth'].dt.to_period('M').astype(str) == cohorte_selection]

    # ===========================
    # 1️⃣ KPIs Baseline
    # ===========================
    clv_baseline = df_sim.groupby('CustomerID')['AmountNet'].sum().mean()
    ca_baseline = df_sim['AmountNet'].sum()
    # Rétention transactionnelle : % de transactions qui sont des ventes (non-retours)
    retention_baseline = (df_sim['IsReturn'] == False).sum() / len(df_sim)

    st.subheader("🔹 KPIs Baseline")
    col1, col2, col3 = st.columns(3)
    col1.metric("CLV moyen (€)", f"{clv_baseline:,.2f}")
    col2.metric("CA total (€)", f"{ca_baseline:,.2f}")
    col3.metric("Rétention (%)", f"{retention_baseline*100:.2f}")

    # ===========================
    # 2️⃣ Calcul scénario
    # ===========================
    # Ajuster montant selon marge et remise au niveau transaction
    df_scenario = df_sim.copy()
    df_scenario['AmountNet_adj'] = df_scenario['AmountNet'] * (1 + marge_pct/100) * (1 - discount_pct/100)

    # Appliquer variation de rétention
    retention_scenario = retention_baseline * (1 + retention_pct/100)
    retention_scenario = min(retention_scenario, 1)  # ne peut pas dépasser 100%

    # CLV et CA scénario corrects
    clv_scenario = df_scenario.groupby('CustomerID')['AmountNet_adj'].sum().mean()
    ca_scenario = df_scenario['AmountNet_adj'].sum()

    # Appliquer variation de rétention sur le KPI uniquement si on veut
    clv_scenario *= retention_scenario / retention_baseline
    ca_scenario *= retention_scenario / retention_baseline

    # 3️⃣ Affichage KPIs Scénario
    # ===========================
    st.subheader("🔹 KPIs Scénario")
    col1, col2, col3 = st.columns(3)
    col1.metric("CLV moyen (€)", f"{clv_scenario:,.2f}", f"{clv_scenario - clv_baseline:,.2f}")
    col2.metric("CA total (€)", f"{ca_scenario:,.2f}", f"{ca_scenario - ca_baseline:,.2f}")
    col3.metric("Rétention (%)", f"{retention_scenario*100:.2f}", f"{(retention_scenario - retention_baseline)*100:.2f}")

    # ===========================
    # 4️⃣ Graphiques mensuels CLV et CA côte à côte
    # ===========================

    st.write("")
    st.write("")
    st.subheader("📈 Représentation visuelle des KPI Baseline/Scénario")

    monthly = df_scenario.groupby(df_scenario['InvoiceMonth'].dt.to_period('M')).agg({
        'AmountNet': ['sum', lambda x: x.sum()/x.nunique()],
        'AmountNet_adj': ['sum', lambda x: x.sum()/x.nunique()]
    })
    monthly.columns = ['CA_baseline', 'CLV_baseline', 'CA_scenario', 'CLV_scenario']
    monthly.index = monthly.index.to_timestamp()

    # 📊 Subplots Plotly
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("CA mensuel", "CLV mensuel")
    )

    # --- CA mensuel ---
    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly['CA_baseline'],
            mode='lines+markers',
            name='CA Baseline'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly['CA_scenario'],
            mode='lines+markers',
            name='CA Scénario'
        ),
        row=1, col=1
    )

    # --- CLV mensuel ---
    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly['CLV_baseline'],
            mode='lines+markers',
            name='CLV Baseline'
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly['CLV_scenario'],
            mode='lines+markers',
            name='CLV Scénario'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=500,
        showlegend=True,
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ===========================
    # 5️⃣ Bar charts CLV / CA Baseline vs Scénario
    # ===========================

    fig2 = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("CLV moyen", "CA total")
    )

    labels = ['Baseline', 'Scénario']
    clv_vals = [clv_baseline, clv_scenario]
    ca_vals = [ca_baseline, ca_scenario]

    # --- Bar chart CLV ---
    fig2.add_trace(
        go.Bar(
            x=labels,
            y=clv_vals,
            text=[f"{v:,.2f}" for v in clv_vals],
            textposition='outside',
            name="CLV"
        ),
        row=1, col=1
    )

    # --- Bar chart CA ---
    fig2.add_trace(
        go.Bar(
            x=labels,
            y=ca_vals,
            text=[f"{v:,.2f}" for v in ca_vals],
            textposition='outside',
            name="CA"
        ),
        row=1, col=2
    )

    fig2.update_layout(
        height=450,
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ==========================
    # ℹ️ AIDE INTÉGRÉE
    # ==========================
    st.write("")
    st.write("")
    with st.expander("ℹ️ Aide intégrée — comprendre les KPI et les paramètres du scénario"):
        st.markdown(
            """
            ## 🧠 Comprendre les KPI & le fonctionnement des scénarios

            Cette section vous aide à comprendre **comment les paramètres du scénario impactent les KPI**
            affichés plus haut : **CLV**, **CA total** et **rétention**.

            ---

            ### 📌 **1. CLV (Customer Lifetime Value)**  
            Le **CLV** représente le montant moyen dépensé par un client durant toute la période analysée.  
            👉 *CLV = Somme des achats par client / Nombre de clients*

            **Exemple :**  
            Si un client a dépensé 280€, un deuxième 320€ → CLV = 300€.

            **Impact des sliders :**  
            - La *variation de marge* augmente ou réduit le montant net par transaction.  
            - La *remise moyenne* réduit le montant payé par le client.  
            - La *variation de rétention* influence la probabilité qu’un client génère de nouvelles transactions.

            ---

            ### 💶 **2. Chiffre d’Affaires (CA total)**  
            Le **CA total** est la somme des montants nets générés sur la période sélectionnée.

            **Exemple :**  
            Si 10 transactions de 50€ → CA = 500€.

            **Impact des sliders :**
            - *Variation de marge* : augmente ou diminue le montant de chaque vente.  
            - *Remise moyenne* : réduit le montant payé.  
            - *Variation de rétention* : plus les clients restent, plus il y a de transactions → CA augmente.

            ---

            ### 🔁 **3. Rétention transactionnelle**  
            Mesure la part des transactions qui ne sont **pas** des retours.  
            👉 *Rétention = Transactions valides / Toutes les transactions*

            **Exemple :**  
            900 transactions valides / 1 000 total → Rétention = 90%.

            **Impact du slider :**  
            Le slider simule une amélioration ou baisse de la rétention client.

            ---

            ### 🛠️ **4. Comment fonctionne la simulation ?**
            Lorsque vous modifiez un paramètre :
            - Le montant de chaque transaction est ajusté → (Marge + Remise)
            - La rétention modifie le volume de transactions simulées
            - Les nouveaux KPI **répondent dynamiquement** à vos paramètres

            ---

            ### 📊 **5. Graphiques**
            - Les **courbes mensuelles** comparent Baseline vs Scénario sur le CA et le CLV.  
            - Les **bar charts** affichent l’impact global sur toute la période.

            Ces visualisations permettent :
            - de comprendre les tendances,  
            - d’identifier les mois les plus sensibles,  
            - et de comparer l'effet total entre *Baseline* et *Scénario*.

            ---

            Si vous souhaitez ajouter plus d’explications ou un tutoriel interactif, je peux vous le générer 😊
            """
        )
