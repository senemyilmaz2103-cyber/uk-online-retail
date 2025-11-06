# User-OAuth BigQuery connect + smoke test

#import pydata_google_auth
#from google.cloud import bigquery
#import pandas_gbq as gbq


#PROJECT_ID = "uk-online-retail-data-project"   # <-- confirm your project id
#SCOPES = [
#   "https://www.googleapis.com/auth/bigquery",
#    "https://www.googleapis.com/auth/cloud-platform",
#]

# 1) Get user credentials via browser; token is cached locally for reuse
#creds = pydata_google_auth.get_user_credentials(SCOPES)

# 2a) BigQuery client using those creds (no gcloud, no JSON key)
#client = bigquery.Client(project=PROJECT_ID, credentials=creds)
#print("Project:", client.project)
#Print("Test:", next(client.query("SELECT 1 AS ok").result()).ok)

# 2b) Or directly to pandas with pandas-gbq (same creds)
#sql = "SELECT * FROM `uk-online-retail-data-project.uk_online_retail.full_features_raw` "

#df = gbq.read_gbq(sql, project_id=PROJECT_ID, credentials=creds)
#print(df.head())
#f.to_csv("full_features_raw.csv", index=False)

####################################### ANALYSIS ########################################

import pandas as pd
from pathlib import Path

CSV_PATH = Path("data/full_features_raw.csv")
df = pd.read_csv(CSV_PATH)

#print("Data shape:", df.shape)
#print("Columns:", df.columns.tolist())
#print("Missing values per column:\n", df.isnull().sum())
#print("Sample data:\n", df.head())

#Columns: ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country', 'category', 'InvoiceDateOnly', 'Year', 'Month', 'Day', 'DayOfWeekNum', 'IsWeekend', 'DayOfWeekName', 'MonthName', 'Season', 'IsReturn', 'TotalPrice']

# Further analysis code would go here

########################## RFM Analysis ###########################

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['CustomerID'] = df['CustomerID'].astype(str)

# Filter out rows with missing CustomerID
df_valid = df[df['CustomerID'].notnull()].copy()

# Convert to string to avoid dtype issues later
df_valid['CustomerID'] = df_valid['CustomerID'].astype(str)

# Reference date (day after the last transaction)
snapshot_date = df_valid['InvoiceDate'].max() + pd.Timedelta(days=1)

# Compute RFM

rfm = df_valid.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,   # Recency
    'InvoiceNo': 'nunique',                                   # Frequency
    'TotalPrice': 'sum'                                       # Monetary
}).rename(columns={'InvoiceDate': 'Recency', 'InvoiceNo': 'Frequency', 'TotalPrice': 'Monetary'})

print("RFM head:\n", rfm.head())

# Save RFM to CSV
rfm.to_csv("data/rfm_analysis.csv")
