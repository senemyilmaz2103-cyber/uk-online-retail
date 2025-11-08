import pandas as pd
import utilities as u
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def _format_id(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text

# Load your dataset
df = pd.read_csv('data/full_features_raw.csv')
df = df[df["UnitPrice"] > 0]

# 1️⃣ Build RFM
rfm = u.Utils.build_rfm(df)

# 2️⃣ Run K-Means (try 4 clusters)
rfm = u.Utils.segment_customers_kmeans(rfm, k=4)

# 3️⃣ See what each cluster looks like
summary = u.Utils.describe_clusters(rfm)

# 4️⃣ Dynamically map clusters to business-friendly labels
default_labels = [
    "Champions / VIPs",
    "Loyal Customers",
    "Potential Loyalists",
    "At Risk",
    "Lost / Hibernating"
]

def _scale(series, invert=False):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(1.0, index=series.index)
    scaled = (series - min_val) / (max_val - min_val)
    if invert:
        scaled = 1 - scaled
    return scaled


ranking = summary.copy()
ranking["RecencyScore"] = _scale(ranking["Recency"], invert=True)
ranking["FrequencyScore"] = _scale(ranking["Frequency"], invert=False)
ranking["MonetaryScore"] = _scale(ranking["Monetary"], invert=False)
ranking["Score"] = ranking["RecencyScore"] + ranking["FrequencyScore"] + ranking["MonetaryScore"]
ordered_clusters = ranking.sort_values("Score", ascending=False).index.tolist()
cluster_names = {
    cluster_id: (default_labels[i] if i < len(default_labels) else f"Segment {i+1}")
    for i, cluster_id in enumerate(ordered_clusters)
}

rfm["Cluster"] = rfm["Cluster"].astype(int)
rfm["Segment"] = rfm["Cluster"].map(cluster_names)

# Ensure CustomerID is exported as string
rfm = rfm.reset_index().rename(columns={"index": "CustomerID"})
rfm["CustomerID"] = rfm["CustomerID"].apply(_format_id)

rfa = rfm[rfm["Monetary"] > 0].copy()
rfa.to_csv("data/rfm_kmeans_results.csv", index=False)

print(rfa.head())
print("\nCluster summary:\n", summary)



# 5️⃣ Evaluate clustering quality with Silhouette Score ranging from -1 to +1. Good scores are > 0.5
scaler = StandardScaler()
X_scaled = scaler.fit_transform(rfm[['Recency','Frequency','Monetary']])

score = silhouette_score(X_scaled, rfm['Cluster'])
print(f"Silhouette Score: {score:.3f}")  # Silhouette Score: 0.614 -- good clustering
