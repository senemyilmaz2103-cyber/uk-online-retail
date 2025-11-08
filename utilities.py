import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

class Utils:
    def filter_valid_customers(df):
        """Removes rows where CustomerID is null."""
        return df[df['CustomerID'].notnull()].copy()

    def compute_rfm(df):
        """Computes Recency, Frequency, Monetary metrics."""
        snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
        rfm = df.groupby('CustomerID').agg({
            'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
            'InvoiceNo': 'nunique',
            'TotalPrice': 'sum'
        }).rename(columns={
            'InvoiceDate': 'Recency',
            'InvoiceNo': 'Frequency',
            'TotalPrice': 'Monetary'
        })
        return rfm

    def score_rfm(rfm):
        """Creates RFM scores (1-5) and total RFM_Score."""
        rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1]).astype(int)
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5]).astype(int)
        rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
        return rfm

    def segment_customers_rule_based(rfm):
        """Segments customers based on RFM_Score."""
        def segment(row):
            s = row['RFM_Score']
            if s >= 12:
                return 'Champions'
            elif s >= 9:
                return 'Loyal Customers'
            elif s >= 6:
                return 'Potential Loyalists'
            elif s >= 4:
                return 'At Risk'
            else:
                return 'Lost'
        rfm['Segment'] = rfm.apply(segment, axis=1)
        return rfm

    def build_customer_profile(df, rfm):
        """
        Creates a customer profile by combining RFM metrics
        with purchase behavior features (habits).
        """
        habits = df.groupby('CustomerID').agg({
            'Quantity': 'sum',
            'StockCode': 'nunique',
            'category': lambda x: x.mode()[0] if len(x.mode()) > 0 else None, # Top category
            'IsWeekend': 'mean',  # % of weekend purchases
        }).rename(columns={
            'Quantity': 'TotalQuantity',
            'TotalPrice': 'TotalSpent',
            'StockCode': 'UniqueProducts',
            'category': 'TopCategory',
            'Country': 'TopCountry',
            'IsWeekend': 'WeekendPurchaseRatio'
        })

        customer_profile = rfm.merge(habits, on='CustomerID', how='left')
        return customer_profile

    # The following functions are retained from segmentation.py for potential reuse  
    

    def build_rfm(df):
        """Create a simple RFM table from your transaction data."""
        df = df[df['CustomerID'].notnull()].copy()
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

        snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

        rfm = df.groupby('CustomerID').agg({
            'InvoiceDate': lambda x: (snapshot_date - x.max()).days,  # Recency
            'InvoiceNo': 'nunique',                                   # Frequency
            'TotalPrice': 'sum'                                       # Monetary
        }).rename(columns={'InvoiceDate': 'Recency', 'InvoiceNo': 'Frequency', 'TotalPrice': 'Monetary'})

        return rfm


    def segment_customers_kmeans(rfm, k=4):
        """Cluster customers using K-Means on R, F, M."""
        scaler = StandardScaler()
        X = scaler.fit_transform(rfm[['Recency', 'Frequency', 'Monetary']])

        kmeans = KMeans(n_clusters=k, random_state=42)
        rfm['Cluster'] = kmeans.fit_predict(X)

        return rfm


    def describe_clusters(rfm):
        """Quick summary showing the average R, F, M for each cluster."""
        return rfm.groupby('Cluster').mean().round(2)

