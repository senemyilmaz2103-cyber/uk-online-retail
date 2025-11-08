import pandas as pd
from recommender_directional import (
    build_directional_pairs,
    recommend_directional,
    top_pairs_with_lift,
    compute_category_priority,

)

df = pd.read_csv("data/full_features_raw.csv")
df = df[df["Quantity"] > 0]
df["StockCode"] = df["StockCode"].astype(str)
df["InvoiceNo"] = df["InvoiceNo"].astype(str)
# optional noise filters
df = df[~df["StockCode"].str.contains("DOT", case=False, na=False)] # remove dotted items
df = df[~df["Description"].str.contains("POSTAGE|CARRIAGE|ADJUST", case=False, na=False)] # remove postage/adjustments

item_count, pair_count = build_directional_pairs(df)

recs = recommend_directional(
    "22346",                # any real StockCode
    item_count, pair_count,
    df,
    top_n=5, min_conf=0.02, min_support=3
)
top_pairs_df = top_pairs_with_lift(
    item_count, pair_count, df,
    top_n=10, min_support=50)
print(top_pairs_df)
top_pairs_df.to_csv("data/top_pairs_with_lift.csv", index=False)
print("OLD VERSION RECS:")
print(recs)

df = pd.read_csv("data/full_features_raw.csv")
df = df[df["Quantity"] > 0]

item_count, pair_count = build_directional_pairs(df)

priority_map = compute_category_priority(df, method="revenue")

recs = recommend_directional(
    base_sku="22346",
    item_count=item_count,
    pair_count=pair_count,
    df=df,
    top_n=5,
    min_support=5,
    min_conf=0.03,
    cat_priority=priority_map,
    enforce_price=True
)
print(recs)
print("NEW VERSION RECS WITH CATEGORY PRIORITY AND PRICE ENFORCEMENT:")