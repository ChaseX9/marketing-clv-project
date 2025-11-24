# 🚀 Marketing CLV Dashboard  

---

##  Présentation du projet

Ce projet consiste à construire une application **Streamlit** complète permettant à une équipe marketing de :

- Diagnostiquer la **rétention par cohortes**
- Piloter la **segmentation clients (RFM)**
- Calculer la **Customer Lifetime Value (CLV)**
- Simuler des **scénarios business** en temps réel
- Exporter des **listes activables** ou visuels marketing

Dataset utilisé : **Online Retail II (UCI)** — 1,07M de transactions (2009–2011).

---

#  Architecture du projet

```
📁 Projet/
│
├── Application/
│   ├── app.py
│   ├── utils.py
│   └── pages/
│       ├── overview.py
│       ├── cohortes.py
│       ├── segments.py
│       ├── scenario.py
│       └── export.py
│
├── data/
│   ├── online_retail_II_clean_scenario.csv
│   └── raw/
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   └── process.ipynb
│
├── requirements.txt
└── README.md
```
---

#  Pages de l’application

##  1. Overview – KPIs Globaux
- Clients actifs  
- CLV baseline  
- CA moyen par âge de cohorte  
- Taille RFM (clients profilés)  
- North Star : CA à 90 jours  
- Courbe CA mensuel (Plotly + barre d'outils)  
- Aide intégrée  

---

##  2. Cohortes – Analyse de rétention
- Heatmap de rétention (Plotly)  
- CA par âge de cohorte  
- Focus par cohorte  
- Rétention M+3  
- CLV empirique  
- CA 90 jours  
- Export CSV / Excel  

---

##  3. Segments – RFM
- Calcul Recency / Frequency / Monetary  
- Scores normalisés 1–5  
- Score RFM concaténé (ex : 554)  
- Tableau RFM exportable  
- Aide intégrée  

---

##  4. Scénarios marketing
Simulation en temps réel de :

- Variation de rétention  
- Variation de la marge  
- Variation des remises  
- Cohorte cible  
- Impact immédiat sur :  
  - **CLV**  
  - **CA**  
  - **Rétention**  

Graphiques comparatifs baseline vs scénario.

---

# 📘 Notebooks

##  01_exploration.ipynb
Analyse exploratoire complète :

- Qualité des données  
- Outliers  
- Retours produits  
- Saisonnalité & tendances  
- Premiers RFM  
- Premières cohortes  

##  process.ipynb
Nettoyage + préparation :

- Colonnes créées : InvoiceMonth, AcquisitionMonth, AmountNet, IsReturn  
- Gestion des retours  
- Sélection finale  

---

#  Reproductibilité

- requirements.txt fourni  
- Notebooks détaillés  
- Arborescence claire  
- Application robuste et modulable  

---

