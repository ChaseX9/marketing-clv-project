# page_cohortes.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Chargement des données ===
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "online_retail_II_clean_scenario.csv")
    df = pd.read_csv(path, parse_dates=['InvoiceDate', 'InvoiceMonth', 'AcquisitionMonth'])
   
    return df

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




# === Filtres ===
st.sidebar.header("Filtres")



# Filtre par niveau géographique
geo_filter = st.sidebar.radio("Filtrer par :", ["Tous", "Continent", "Pays"])

if geo_filter == "Continent":
    continent_choice = st.sidebar.selectbox("Choisir un continent", sorted(df["Continent"].unique()))
    df = df[df["Continent"] == continent_choice]
elif geo_filter == "Pays":
    pays_choice = st.sidebar.multiselect("Choisir un ou plusieurs pays", options=sorted(df["Country"].unique()))
    if pays_choice:
        df = df[df["Country"].isin(pays_choice)]



# Filtre par cohortes
cohortes = sorted(df["AcquisitionMonth"].dt.strftime("%Y-%m").unique())
selected_cohortes = st.sidebar.multiselect("Sélectionner des cohortes", options=cohortes, default=cohortes)
df = df[df["AcquisitionMonth"].dt.strftime("%Y-%m").isin(selected_cohortes)]


# === Calcul des cohortes ===
df["CohortAge"] = ((df["InvoiceMonth"].dt.year - df["AcquisitionMonth"].dt.year) * 12 +
                   (df["InvoiceMonth"].dt.month - df["AcquisitionMonth"].dt.month))

cohort_data = df.groupby(["AcquisitionMonth", "CohortAge"])["CustomerID"].nunique().reset_index()
cohort_sizes = cohort_data[cohort_data["CohortAge"] == 0][["AcquisitionMonth", "CustomerID"]].rename(columns={"CustomerID": "CohortSize"})
cohort_data = cohort_data.merge(cohort_sizes, on="AcquisitionMonth")
cohort_data["RetentionRate"] = cohort_data["CustomerID"] / cohort_data["CohortSize"]

# === Heatmap rétention ===
retention_matrix = cohort_data.pivot(index="AcquisitionMonth", columns="CohortAge", values="RetentionRate")
fig_heatmap = px.imshow(retention_matrix,
                        labels=dict(x="Âge de cohorte (mois)", y="Mois d'acquisition", color="Taux de rétention"),
                        x=retention_matrix.columns,
                        y=retention_matrix.index,
                        color_continuous_scale="Blues")
fig_heatmap.update_layout(title="Heatmap de rétention par cohortes")

# === Courbe CA par âge ===
revenue_data = df.groupby(["CohortAge"])["AmountNet"].sum().reset_index()
fig_revenue = px.line(revenue_data, x="CohortAge", y="AmountNet",
                      labels={"CohortAge": "Âge de cohorte (mois)", "AmountNet": "CA net"},
                      title="Dynamique du CA par âge de cohorte")

# === Affichage ===
st.title("📊 Analyse des Cohortes")
st.plotly_chart(fig_heatmap, use_container_width=True)
st.plotly_chart(fig_revenue, use_container_width=True)


# === Focus sur une cohorte ===
st.subheader("Focus sur une cohorte")
cohorte_select = st.selectbox("Choisir une cohorte", options=selected_cohortes)
focus_data = df[df["AcquisitionMonth"].dt.strftime("%Y-%m") == cohorte_select]
focus_revenue = focus_data.groupby("CohortAge")["AmountNet"].sum().reset_index()
fig_focus = px.bar(focus_revenue, x="CohortAge", y="AmountNet",
                   labels={"CohortAge": "Âge (mois)", "AmountNet": "CA net"},
                   title=f"CA par âge pour la cohorte {cohorte_select}")
st.plotly_chart(fig_focus, use_container_width=True)




# === Indicateurs clés ===
st.subheader("📈 Indicateurs clés")

# CLV moyenne
clv_moyenne = df.groupby("CustomerID")["AmountNet"].sum().mean()

# CA à 90 jours par nouveau client
df["DaysSinceAcquisition"] = (df["InvoiceDate"] - df["AcquisitionMonth"]).dt.days
ca_90 = df[df["DaysSinceAcquisition"] <= 90].groupby("CustomerID")["AmountNet"].sum().mean()

# Rétention M+3
retention_m3 = cohort_data[cohort_data["CohortAge"] == 3]["RetentionRate"].mean() * 100

# CLV empirique (observée)
clv_empirique = df.groupby("CustomerID")["AmountNet"].sum().mean()

# CLV formule fermée (exemple avec marge=10€, r=0.8, d=0.1)
marge = 10
r = 0.8
d = 0.1
clv_formula = (marge * r) / (1 + d - r)

# Affichage des métriques
st.metric("CLV moyenne", f"{clv_moyenne:.2f} €")
st.metric("CA à 90 jours", f"{ca_90:.2f} €")
st.metric("Rétention M+3", f"{retention_m3:.1f} %")
st.metric("CLV empirique", f"{clv_empirique:.2f} €")
st.metric("CLV (formule)", f"{clv_formula:.2f} €")



# Calcul RFM
rfm = df.groupby("CustomerID").agg({
    "InvoiceDate": lambda x: (df["InvoiceDate"].max() - x.max()).days,  # Recency
    "InvoiceNo": "count",  # Frequency
    "AmountNet": "sum"  # Monetary
}).rename(columns={"InvoiceDate": "Recency", "InvoiceNo": "Frequency", "AmountNet": "Monetary"})

# Normalisation en scores (1-5)
rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1])
rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])
rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1,2,3,4,5])
rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)

st.write("Tableau RFM", rfm.head())




