# User-OAuth BigQuery connect + smoke test

import pydata_google_auth
from google.cloud import bigquery
import pandas_gbq as gbq

PROJECT_ID = "uk-online-retail-data-project"   # <-- confirm your project id
SCOPES = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform",
]

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

import pandas as pd
from pathlib import Path

CSV_PATH = Path("/Users/arguncankatergun/uk_analiz_python/uk-online-retail/full_features_raw.csv")
df = pd.read_csv(CSV_PATH)
print(df.shape, df.dtypes.head())
print(df.head())