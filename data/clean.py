# data/clean.py
import os
import pandas as pd

# ===========================
# Chemins de fichiers
# ===========================
current_dir = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.join(current_dir, "online_retail_II.csv")
output_csv = os.path.join(current_dir, "online_retail_II_clean.csv")

# ===========================
# Charger le CSV
# ===========================
df = pd.read_csv(input_csv, encoding='ISO-8859-1', parse_dates=['InvoiceDate'])
print(f"CSV chargé avec succès : {input_csv}")

# ===========================
# Nettoyage de base
# ===========================
# Supprimer les lignes sans InvoiceNo ou CustomerID
df = df.dropna(subset=['Invoice', 'Customer ID'])

# Supprimer doublons exacts
df = df.drop_duplicates()

# Renommer colonnes pour plus de clarté
df.rename(columns={
    'Invoice': 'InvoiceNo',
    'Customer ID': 'CustomerID',
    'StockCode': 'StockCode',
    'Description': 'Description',
    'Quantity': 'Quantity',
    'InvoiceDate': 'InvoiceDate',
    'Price': 'UnitPrice',
    'Country': 'Country'
}, inplace=True)

# ===========================
# Conversion des types
# ===========================
df['Quantity'] = df['Quantity'].astype(int)
df['UnitPrice'] = df['UnitPrice'].astype(float)
df['Amount'] = df['Quantity'] * df['UnitPrice']
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')

# ===========================
# Marquer les retours
# ===========================
df['IsReturn'] = df['InvoiceNo'].astype(str).str.startswith('C')

# ===========================
# Ajouter colonne InvoiceMonth pour cohortes
# ===========================
df['InvoiceMonth'] = df['InvoiceDate'].values.astype('datetime64[M]')

# ===========================
# Sauvegarder CSV nettoyé
# ===========================
df.to_csv(output_csv, index=False)
print(f"CSV nettoyé créé : {output_csv}")
print(f"Nombre de lignes après nettoyage : {len(df)}")
