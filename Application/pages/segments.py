# pages/segments.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ===========================
# CHARGEMENT DES DONNÉES
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


# ===========================
# CALCUL RFM
# ===========================
def compute_rfm(df, include_returns=True):
    """
    Calcule les scores RFM pour chaque client
    
    Args:
        df: DataFrame des transactions
        include_returns: Inclure ou non les retours dans le calcul
    
    Returns:
        DataFrame avec les scores RFM
    """
    df_temp = df.copy()
    
    # Filtrer les retours si nécessaire
    if not include_returns:
        df_temp = df_temp[df_temp['IsReturn'] == False]
    
    snapshot_date = df_temp['InvoiceDate'].max() + pd.Timedelta(days=1)
    
    # Calculer RFM
    rfm = df_temp.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days,  # Recency
        'InvoiceNo': 'nunique',  # Frequency
        'AmountNet': 'sum'  # Monetary
    }).rename(columns={
        'InvoiceDate': 'Recency',
        'InvoiceNo': 'Frequency',
        'AmountNet': 'Monetary'
    })
    
    # Filtrer les montants négatifs (clients qui ont plus de retours que d'achats)
    rfm = rfm[rfm['Monetary'] > 0]
    
    # Créer les scores (1-5)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    
    # Score RFM combiné
    rfm['RFM_Score'] = (rfm['R_Score'].astype(str) + 
                        rfm['F_Score'].astype(str) + 
                        rfm['M_Score'].astype(str))
    
    # Score numérique pour le tri
    rfm['RFM_Numeric'] = (rfm['R_Score'].astype(int) + 
                          rfm['F_Score'].astype(int) + 
                          rfm['M_Score'].astype(int))
    
    return rfm


# ===========================
# SEGMENTATION RFM
# ===========================
def segment_rfm(rfm):
    """
    Attribue un segment à chaque client basé sur son score RFM
    
    Args:
        rfm: DataFrame avec les scores RFM
    
    Returns:
        DataFrame avec la colonne Segment ajoutée
    """
    rfm = rfm.copy()
    
    def assign_segment(row):
        r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
        
        # Champions : meilleurs clients
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        
        # Loyaux : bonne fréquence et valeur, mais pas très récent
        elif r >= 3 and f >= 4 and m >= 4:
            return 'Loyaux'
        
        # Potentiels Loyaux : récents avec bonne fréquence
        elif r >= 4 and f >= 3 and m >= 3:
            return 'Potentiels Loyaux'
        
        # Nouveaux : très récents mais faible fréquence
        elif r >= 4 and f <= 2:
            return 'Nouveaux'
        
        # Prometteurs : récents avec valeur moyenne
        elif r >= 3 and f <= 2 and m >= 3:
            return 'Prometteurs'
        
        # Besoin d'attention : bons scores mais commencent à décliner
        elif r == 3 and f >= 3 and m >= 3:
            return 'Besoin d\'Attention'
        
        # À risque : étaient bons mais deviennent inactifs
        elif r <= 2 and f >= 3 and m >= 3:
            return 'À Risque'
        
        # Hibernants : pas vus depuis longtemps, faible engagement
        elif r <= 2 and f <= 2 and m >= 3:
            return 'Hibernants'
        
        # Perdus : inactifs, faible valeur
        elif r <= 2 and f <= 2 and m <= 2:
            return 'Perdus'
        
        # Autres
        else:
            return 'Autres'
    
    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    return rfm


# ===========================
# PRIORITÉS D'ACTIVATION
# ===========================
def get_segment_priorities():
    """
    Retourne les priorités et actions recommandées pour chaque segment
    """
    priorities = {
        'Champions': {
            'priority': 1,
            'color': '#2ecc71',
            'action': 'Récompenser, solliciter avis, upsell premium',
            'description': 'Meilleurs clients, très actifs et dépensent beaucoup'
        },
        'Loyaux': {
            'priority': 2,
            'color': '#27ae60',
            'action': 'Programmes fidélité, offres exclusives',
            'description': 'Clients fidèles avec bonne valeur'
        },
        'Potentiels Loyaux': {
            'priority': 3,
            'color': '#3498db',
            'action': 'Engagement régulier, offres personnalisées',
            'description': 'Récents avec bon potentiel de fidélisation'
        },
        'Nouveaux': {
            'priority': 4,
            'color': '#9b59b6',
            'action': 'Onboarding, offres découverte, formation',
            'description': 'Clients récents à convertir'
        },
        'Prometteurs': {
            'priority': 5,
            'color': '#1abc9c',
            'action': 'Offres ciblées, cross-sell',
            'description': 'Bon potentiel de valeur'
        },
        'Besoin d\'Attention': {
            'priority': 6,
            'color': '#f39c12',
            'action': 'Campagnes de réengagement, enquêtes satisfaction',
            'description': 'Commencent à décliner, à réactiver rapidement'
        },
        'À Risque': {
            'priority': 7,
            'color': '#e67e22',
            'action': 'Offres de reconquête, remises limitées',
            'description': 'Étaient bons mais deviennent inactifs'
        },
        'Hibernants': {
            'priority': 8,
            'color': '#e74c3c',
            'action': 'Campagnes de réactivation, win-back',
            'description': 'Inactifs depuis longtemps'
        },
        'Perdus': {
            'priority': 9,
            'color': '#95a5a6',
            'action': 'Coût faible : sondage ou retrait liste',
            'description': 'Très peu d\'engagement, ROI faible'
        },
        'Autres': {
            'priority': 10,
            'color': '#7f8c8d',
            'action': 'À analyser au cas par cas',
            'description': 'Profil mixte'
        }
    }
    return priorities


# ===========================
# CALCUL MÉTRIQUES PAR SEGMENT
# ===========================
def compute_segment_metrics(df, rfm):
    """
    Calcule les métriques business par segment
    """
    # Joindre les segments aux transactions
    df_with_segment = df.merge(
        rfm[['Segment']].reset_index(),
        on='CustomerID',
        how='inner'
    )
    
    # Agréger par segment
    metrics = df_with_segment.groupby('Segment').agg({
        'CustomerID': 'nunique',
        'AmountNet': ['sum', 'mean'],
        'InvoiceNo': 'nunique'
    }).reset_index()
    
    metrics.columns = ['Segment', 'Clients', 'CA_Total', 'Panier_Moyen', 'Transactions']
    
    # Calculer part du CA
    metrics['Part_CA'] = (metrics['CA_Total'] / metrics['CA_Total'].sum() * 100)
    
    # Ajouter les priorités
    priorities = get_segment_priorities()
    metrics['Priorité'] = metrics['Segment'].map(lambda x: priorities[x]['priority'])
    metrics['Action'] = metrics['Segment'].map(lambda x: priorities[x]['action'])
    
    # Trier par priorité
    metrics = metrics.sort_values('Priorité')
    
    return metrics


# ===========================
# PAGE PRINCIPALE
# ===========================
def show():
    st.title("🎯 Segments RFM - Priorisation des Actions")
    
    # Charger les données
    df = load_data()
    
    # ===========================
    # FILTRES SIDEBAR
    # ===========================
    st.sidebar.header("Filtres")
    
    # Filtre retours
    include_returns = st.sidebar.checkbox("Inclure les retours dans le calcul RFM", value=True)
    
    # Filtre période
    min_date = df['InvoiceDate'].min().date()
    max_date = df['InvoiceDate'].max().date()
    
    date_range = st.sidebar.date_input(
        "Période d'analyse",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        df = df[(df['InvoiceDate'].dt.date >= date_range[0]) & 
                (df['InvoiceDate'].dt.date <= date_range[1])]
    
    # Filtre pays
    countries = ['Tous'] + sorted(df['Country'].unique().tolist())
    selected_country = st.sidebar.selectbox("Pays", countries)
    
    if selected_country != 'Tous':
        df = df[df['Country'] == selected_country]
    
    # Badge filtres actifs
    if not include_returns:
        st.sidebar.info("⚠️ Retours exclus")
    
    # ===========================
    # CALCUL RFM
    # ===========================
    rfm = compute_rfm(df, include_returns)
    rfm = segment_rfm(rfm)
    metrics = compute_segment_metrics(df, rfm)
    
    # ===========================
    # SECTION 1 : VUE D'ENSEMBLE
    # ===========================
    st.markdown("---")
    st.subheader("📊 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clients", f"{len(rfm):,}".replace(',', ' '))
    
    with col2:
        ca_total = metrics['CA_Total'].sum()
        st.metric("CA Total", f"{ca_total:,.0f} €".replace(',', ' '))
    
    with col3:
        panier_moyen = df.groupby('InvoiceNo')['AmountNet'].sum().mean()
        st.metric("Panier Moyen", f"{panier_moyen:,.2f} €".replace(',', ' '))
    
    with col4:
        nb_segments = rfm['Segment'].nunique()
        st.metric("Segments Actifs", nb_segments)
    
    # ===========================
    # SECTION 2 : DISTRIBUTION DES SEGMENTS
    # ===========================
    st.markdown("---")
    st.subheader("📈 Distribution des Segments")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique en barres : nombre de clients par segment
        fig_clients = px.bar(
            metrics,
            x='Segment',
            y='Clients',
            title='Nombre de clients par segment',
            color='Segment',
            color_discrete_map={seg: get_segment_priorities()[seg]['color'] 
                               for seg in metrics['Segment']},
            text='Clients'
        )
        fig_clients.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_clients.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_clients, use_container_width=True)
    
    with col2:
        # Graphique en barres : CA par segment
        fig_ca = px.bar(
            metrics,
            x='Segment',
            y='CA_Total',
            title='CA total par segment',
            color='Segment',
            color_discrete_map={seg: get_segment_priorities()[seg]['color'] 
                               for seg in metrics['Segment']},
            text='CA_Total'
        )
        fig_ca.update_traces(texttemplate='%{text:,.0f}€', textposition='outside')
        fig_ca.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_ca, use_container_width=True)
    
    # ===========================
    # SECTION 3 : TABLEAU DES SEGMENTS
    # ===========================
    st.markdown("---")
    st.subheader("📋 Table RFM détaillée")
    
    # Préparer le tableau pour l'affichage
    display_metrics = metrics.copy()
    display_metrics['CA_Total'] = display_metrics['CA_Total'].apply(lambda x: f"{x:,.0f} €")
    display_metrics['Panier_Moyen'] = display_metrics['Panier_Moyen'].apply(lambda x: f"{x:,.2f} €")
    display_metrics['Part_CA'] = display_metrics['Part_CA'].apply(lambda x: f"{x:.1f}%")
    
    # Réorganiser les colonnes
    display_metrics = display_metrics[[
        'Priorité', 'Segment', 'Clients', 'CA_Total', 
        'Part_CA', 'Panier_Moyen', 'Transactions', 'Action'
    ]]
    
    # Afficher le tableau avec style
    st.dataframe(
        display_metrics,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Priorité": st.column_config.NumberColumn("Priorité", help="1 = Haute priorité"),
            "Segment": st.column_config.TextColumn("Segment", width="medium"),
            "Clients": st.column_config.NumberColumn("Clients", format="%d"),
            "CA_Total": st.column_config.TextColumn("CA Total"),
            "Part_CA": st.column_config.TextColumn("Part CA"),
            "Panier_Moyen": st.column_config.TextColumn("Panier Moyen"),
            "Transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "Action": st.column_config.TextColumn("Action Recommandée", width="large")
        }
    )
    
    # ===========================
    # SECTION 4 : PRIORITÉS D'ACTIVATION
    # ===========================
    st.markdown("---")
    st.subheader("🎯 Priorités d'Activation")
    
    # Top 3 segments à activer
    top3 = metrics.nsmallest(3, 'Priorité')
    
    for idx, row in top3.iterrows():
        segment = row['Segment']
        priorities = get_segment_priorities()
        
        with st.expander(f"🔥 Priorité {row['Priorité']} : {segment} ({row['Clients']} clients)"):
            st.markdown(f"**Description :** {priorities[segment]['description']}")
            st.markdown(f"**Action recommandée :** {priorities[segment]['action']}")
            st.markdown(f"**CA généré :** {row['CA_Total']:,.0f} € ({row['Part_CA']:.1f}% du total)")
            st.markdown(f"**Panier moyen :** {row['Panier_Moyen']:,.2f} €")
    
    # ===========================
    # SECTION 5 : GRAPHIQUE 3D RFM
    # ===========================
    st.markdown("---")
    st.subheader("🔬 Visualisation 3D : Recency × Frequency × Monetary")
    
    # Échantillonner si trop de points
    rfm_sample = rfm if len(rfm) <= 1000 else rfm.sample(1000)
    
    fig_3d = px.scatter_3d(
        rfm_sample.reset_index(),
        x='Recency',
        y='Frequency',
        z='Monetary',
        color='Segment',
        color_discrete_map={seg: get_segment_priorities()[seg]['color'] 
                           for seg in rfm_sample['Segment'].unique()},
        hover_data=['CustomerID', 'RFM_Score'],
        title='Distribution 3D des clients (échantillon)',
        labels={
            'Recency': 'Recency (jours)',
            'Frequency': 'Frequency (transactions)',
            'Monetary': 'Monetary (€)'
        }
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # ===========================
    # SECTION 6 : AIDE ET DÉFINITIONS
    # ===========================
    st.markdown("---")
    with st.expander("ℹ️ Aide : Comprendre les métriques RFM"):
        st.markdown("""
        ### Définitions RFM
        
        - **Recency (R)** : Nombre de jours depuis le dernier achat
            - Score 5 : très récent (meilleur)
            - Score 1 : ancien (moins bon)
            - *Exemple : Un client qui a acheté il y a 10 jours aura un meilleur score qu'un client ayant acheté il y a 200 jours*
        
        - **Frequency (F)** : Nombre de transactions effectuées
            - Score 5 : très fréquent (meilleur)
            - Score 1 : rare (moins bon)
            - *Exemple : Un client avec 20 commandes aura un meilleur score qu'un client avec 2 commandes*
        
        - **Monetary (M)** : Montant total dépensé
            - Score 5 : valeur élevée (meilleur)
            - Score 1 : valeur faible (moins bon)
            - *Exemple : Un client ayant dépensé 5000€ aura un meilleur score qu'un client ayant dépensé 100€*
        
        ### Segments clés
        
        - **Champions** (555) : Vos meilleurs clients → Récompensez-les !
        - **À Risque** (2XX-3XX) : Clients en perte de vitesse → Réengagez-les rapidement
        - **Nouveaux** (5X1-5X2) : Nouveaux clients → Convertissez-les en clients fidèles
        - **Perdus** (1X1) : Inactifs → ROI faible, limitez les investissements
        
        ### Utilisation
        
        Utilisez cette page pour :
        1. Identifier les segments à forte valeur
        2. Prioriser vos actions marketing
        3. Allouer votre budget CRM efficacement
        4. Exporter des listes pour l'activation
        """)
    
    # ===========================
    # SECTION 7 : EXPORT
    # ===========================
    st.markdown("---")
    st.subheader("💾 Export des données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exporter la table RFM complète"):
            csv = rfm.reset_index().to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger RFM.csv",
                data=csv,
                file_name='rfm_segments.csv',
                mime='text/csv'
            )
    
    with col2:
        # Export liste activable (top segments)
        top_segments = ['Champions', 'Loyaux', 'Potentiels Loyaux', 'Besoin d\'Attention']
        if st.button("📥 Exporter liste activable (top segments)"):
            activable = rfm[rfm['Segment'].isin(top_segments)].reset_index()
            activable = activable[['CustomerID', 'Segment', 'Recency', 'Frequency', 'Monetary', 'RFM_Score']]
            csv = activable.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger liste_activable.csv",
                data=csv,
                file_name='liste_activable.csv',
                mime='text/csv'
            )