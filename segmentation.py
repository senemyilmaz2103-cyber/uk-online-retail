import pandas as pd
import utilities as u  
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Load your dataset
df = pd.read_csv('data/full_features_raw.csv')

# 1️⃣ Build RFM
rfm = u.Utils.build_rfm(df)

# 2️⃣ Run K-Means (try 4 clusters)
rfm = u.Utils.segment_customers(rfm, k=4)

# 3️⃣ See what each cluster looks like
summary = u.Utils.describe_clusters(rfm)

# 4️⃣ Map cluster numbers to meaningful names
cluster_names = {
    0: "Loyal Customers",
    1: "Lost / At Risk",
    2: "Champions / VIPs",
    3: "Potential Loyalists"
}

rfm["Cluster"] = rfm["Cluster"].astype(int)  # güvenli olsun, map anahtarları int
rfm["Segment"] = rfm["Cluster"].map(cluster_names)

print(rfm.head())
print("\nCluster summary:\n", summary)

rfm.to_csv("data/rfm_kmeans_results.csv", index=True)



# 5️⃣ Evaluate clustering quality with Silhouette Score ranging from -1 to +1. Good scores are > 0.5
scaler = StandardScaler()
X_scaled = scaler.fit_transform(rfm[['Recency','Frequency','Monetary']])

score = silhouette_score(X_scaled, rfm['Cluster'])
print(f"Silhouette Score: {score:.3f}")  # Silhouette Score: 0.614 -- good clustering
