# app/scenarios.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# ===========================
# Charger les données clean
# ===========================
@st.cache_data
def load_data():
    path = os.path.join("..", "data", "online_retail_II_clean_scenario.csv")
    df = pd.read_csv(path, parse_dates=['InvoiceDate', 'InvoiceMonth', 'AcquisitionMonth'])
    df['CustomerID'] = df['CustomerID'].astype(int)
    if 'AmountNet' not in df.columns:
        df['AmountNet'] = df['Amount']
    return df

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

## CLV et CA scénario corrects
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
st.subheader("📈 Représentation visuelle des KPI")

monthly = df_scenario.groupby(df_scenario['InvoiceMonth'].dt.to_period('M')).agg({
    'AmountNet': ['sum', lambda x: x.sum()/x.nunique()],
    'AmountNet_adj': ['sum', lambda x: x.sum()/x.nunique()]
})
monthly.columns = ['CA_baseline', 'CLV_baseline', 'CA_scenario', 'CLV_scenario']
monthly.index = monthly.index.to_timestamp()

fig, ax = plt.subplots(1, 2, figsize=(16, 6), facecolor='none')  # 1 ligne, 2 colonnes

# CA mensuel
ax[0].plot(monthly.index, monthly['CA_baseline'], label='CA Baseline', color='#1f77b4', marker='o')
ax[0].plot(monthly.index, monthly['CA_scenario'], label='CA Scénario', color='#ff7f0e', marker='o')
ax[0].set_title('CA mensuel', color='white')
ax[0].set_ylabel('CA (€)', color='white')
ax[0].legend()
ax[0].tick_params(axis='x', rotation=45, colors='white')
ax[0].tick_params(axis='y', colors='white')
ax[0].grid(alpha=0.3)
ax[0].set_facecolor('none')

# CLV mensuel
ax[1].plot(monthly.index, monthly['CLV_baseline'], label='CLV Baseline', color='#1f77b4', marker='o')
ax[1].plot(monthly.index, monthly['CLV_scenario'], label='CLV Scénario', color='#ff7f0e', marker='o')
ax[1].set_title('CLV mensuel', color='white')
ax[1].set_ylabel('CLV (€)', color='white')
ax[1].legend()
ax[1].tick_params(axis='x', rotation=45, colors='white')
ax[1].tick_params(axis='y', colors='white')
ax[1].grid(alpha=0.3)
ax[1].set_facecolor('none')

st.pyplot(fig)


# ===========================
# 5️⃣ Bar charts CLV / CA Baseline vs Scénario
# ===========================
fig2, ax2 = plt.subplots(1, 2, figsize=(12, 4), facecolor='none')

# Données et couleurs
labels = ['Baseline', 'Scénario']
clv_vals = [clv_baseline, clv_scenario]
ca_vals = [ca_baseline, ca_scenario]
colors = ['#1f77b4', '#ff7f0e']

# Bar chart CLV
bars0 = ax2[0].bar(labels, clv_vals, color=colors)
ax2[0].set_title('CLV moyen', color='white')
ax2[0].tick_params(axis='y', colors='white')
ax2[0].tick_params(axis='x', colors='white')
ax2[0].set_facecolor('none')

# Ajouter les valeurs au-dessus des barres
for bar, val in zip(bars0, clv_vals):
    height = bar.get_height()
    ax2[0].text(bar.get_x() + bar.get_width()/2, height, f'{val:,.2f}', ha='center', va='bottom', color='white')

# Bar chart CA
bars1 = ax2[1].bar(labels, ca_vals, color=colors)
ax2[1].set_title('CA total', color='white')
ax2[1].tick_params(axis='y', colors='white')
ax2[1].tick_params(axis='x', colors='white')
ax2[1].set_facecolor('none')

# Ajouter les valeurs au-dessus des barres
for bar, val in zip(bars1, ca_vals):
    height = bar.get_height()
    ax2[1].text(bar.get_x() + bar.get_width()/2, height, f'{val:,.2f}', ha='center', va='bottom', color='white')

st.pyplot(fig2)

st.write("")
st.write("")
# ===========================
# 6️⃣ Export des données CSV
# ===========================
st.subheader("💾 Exporter les données")

if st.button("Exporter en CSV"):
    csv = df_scenario.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger le CSV",
        data=csv,
        file_name='scenario_data.csv',
        mime='text/csv'
    )
