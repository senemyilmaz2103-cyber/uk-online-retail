# recommender_directional.py
import pandas as pd
from itertools import combinations

def build_directional_pairs(df, invoice_col="InvoiceNo", item_col="StockCode"):
    """
    Build directional co-purchase stats: counts of (A,B) where A,B appear together.
    Returns two dicts:
      item_count[A] = how many invoices had A
      pair_count[(A,B)] = how many invoices had both A,B
    """
    # Group by invoice to get baskets of items
    baskets = (df[[invoice_col, item_col]]
               .astype({invoice_col:str, item_col:str})
               .groupby(invoice_col)[item_col]
               .apply(lambda s: sorted(set(s))))

    item_count = {}
    pair_count = {}
    for items in baskets:
        for a in items:
            item_count[a] = item_count.get(a, 0) + 1
        for a, b in combinations(items, 2):
            pair_count[(a,b)] = pair_count.get((a,b), 0) + 1
            # ❌ no pair_count[(b,a)] — we keep direction

    return item_count, pair_count


def recommend_directional(a, item_count, pair_count, df,
                          id_col="StockCode", desc_col="Description", cat_col="category",
                          top_n=5, min_conf=0.02, min_support=2):
    N = df["InvoiceNo"].nunique()
    a = str(a)
    sup_a = item_count.get(a, 0)
    if sup_a == 0:
        return pd.DataFrame(columns=["StockCode","Description","Category","Confidence","Lift","Count","Interpretation"])

    rows = []
    for (x, y), c in pair_count.items():
        if x != a or c < min_support:
            continue
        sup_b = item_count.get(y, 0)
        if sup_b == 0:
            continue
        conf = c / sup_a
        lift = conf / (sup_b / N)
        rows.append((y, conf, lift, c, _interpret(conf, lift)))

    recs = (pd.DataFrame(rows, columns=[id_col,"Confidence","Lift","Count","Interpretation"]) #Recommendations
              .sort_values(["Confidence","Lift","Count"], ascending=False)
              .head(top_n))

    if recs.empty:
        return recs

    meta = df[[id_col, desc_col, cat_col]].drop_duplicates()
    recs = recs.merge(meta, on=id_col, how="left")
    return recs[[id_col, desc_col, cat_col, "Confidence","Lift","Count","Interpretation"]] \
               .rename(columns={id_col:"StockCode", desc_col:"Description", cat_col:"Category"}) \
               .reset_index(drop=True)



# Helper function to get top pairs across all items
def top_pairs(item_count, pair_count, df, top_n=10, min_support=5):
    rows = []
    for (a, b), c in pair_count.items():
        if c < min_support:
            continue
        sup_a = item_count.get(a, 0)
        if sup_a == 0:
            continue
        conf = c / sup_a
        rows.append((a, b, conf, c))

    top = (
        pd.DataFrame(rows, columns=["Base", "Recommended", "Confidence", "Count"])
        .sort_values(["Confidence", "Count"], ascending=False)
        .head(top_n)
    )

    # Add item metadata
    meta = df[["StockCode", "Description", "category"]].drop_duplicates()
    top = (
        top.merge(meta, left_on="Base", right_on="StockCode", how="left")
        .rename(columns={"Description": "Base_Description", "category": "Base_Category"})
        .drop(columns="StockCode")
        .merge(meta, left_on="Recommended", right_on="StockCode", how="left")
        .rename(columns={"Description": "Rec_Description", "category": "Rec_Category"})
        .drop(columns="StockCode")
    )

    return top[
        ["Base", "Base_Description", "Base_Category",
         "Recommended", "Rec_Description", "Rec_Category",
         "Confidence", "Count"]
    ]
# Helper function to interpret confidence and lift
def _interpret(conf, lift):
    if conf >= 0.30 and lift >= 2.0:
        return "Strong (bundle)"
    if conf >= 0.15 and lift >= 1.5:
        return "Moderate"
    if conf >= 0.05 and lift >= 1.2:
        return "Weak+"
    return "Unremarkable"

# Additional helper function to get top pairs with lift
def top_pairs_with_lift(item_count, pair_count, df, top_n=20, min_support=5):
    N = df["InvoiceNo"].nunique()
    rows = []
    for (a, b), c in pair_count.items():
        if c < min_support:
            continue
        sup_a = item_count.get(a, 0)
        sup_b = item_count.get(b, 0)
        if sup_a == 0 or sup_b == 0:
            continue
        conf = c / sup_a                            # P(B|A)
        lift = conf / (sup_b / N)                   # confidence / support(B)
        rows.append((a, b, conf, c, lift, _interpret(conf, lift)))

    top = (pd.DataFrame(rows, columns=["Base","Recommended","Confidence","Count","Lift","Interpretation"])
             .sort_values(["Lift","Confidence","Count"], ascending=False)
             .head(top_n))

    meta = df[["StockCode","Description","category"]].drop_duplicates()
    top = (top.merge(meta, left_on="Base", right_on="StockCode", how="left")
              .rename(columns={"Description":"Base_Description","category":"Base_Category"})
              .drop(columns="StockCode")
              .merge(meta, left_on="Recommended", right_on="StockCode", how="left")
              .rename(columns={"Description":"Rec_Description","category":"Rec_Category"})
              .drop(columns="StockCode"))

    return top[["Base","Base_Description","Base_Category",
                "Recommended","Rec_Description","Rec_Category",
                "Confidence","Lift","Count","Interpretation"]]



########################  # End of recommender_directional.py ########################
# Below are the contents of recommender_directional.py


import pandas as pd
from collections import defaultdict
from itertools import combinations

def build_directional_pairs(df,
                            invoice_col="InvoiceNo",
                            item_col="StockCode",
                            order_cols=("InvoiceDate", "StockCode")):
    """
    Counts every co-purchased pair in both directions while preserving
    per-invoice ordering.
    """
    df = (df.dropna(subset=[invoice_col, item_col])
            .astype({invoice_col: str, item_col: str})
            .copy())
    sort_cols = [c for c in (invoice_col,) + tuple(order_cols) if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols)

    baskets = (
        df.groupby(invoice_col)[item_col]
          .apply(lambda s: list(dict.fromkeys(s)))   # keep order, drop duplicates
    )

    item_count = defaultdict(int)
    pair_count = defaultdict(int)

    for items in baskets:
        for sku in items:
            item_count[sku] += 1
        for a, b in combinations(items, 2):
            pair_count[(a, b)] += 1
            pair_count[(b, a)] += 1   # keep direction

    return dict(item_count), dict(pair_count)


def compute_category_priority(df,
                              category_col="category",
                              value_col="TotalPrice",
                              method="revenue"):
    """
    Builds a category->priority map automatically.
    method:
      - 'revenue': higher total revenue = higher priority
      - 'count': higher invoice count = higher priority
      - 'lead_ratio': share of times category appears earlier than others within invoices
    """
    if method == "revenue":
        agg = df.groupby(category_col)[value_col].sum()
    elif method == "count":
        agg = df.groupby(category_col)["InvoiceNo"].nunique()
    elif method == "lead_ratio":
        tmp = (df.sort_values(["InvoiceNo", "InvoiceDate"])
                 .assign(pos=lambda x: x.groupby("InvoiceNo").cumcount()))
        agg = 1 - tmp.groupby(category_col)["pos"].mean() / tmp["pos"].max()
    else:
        raise ValueError("Unknown method")

    ranks = agg.rank(ascending=False, method="dense").astype(int)
    return ranks.to_dict()


def recommend_directional(base_sku,
                          item_count,
                          pair_count,
                          df,
                          id_col="StockCode",
                          desc_col="Description",
                          cat_col="category",
                          price_col="UnitPrice",
                          top_n=5,
                          min_support=3,
                          min_conf=0.02,
                          cat_priority=None,
                          enforce_price=False):
    """
    Produces directional recommendations with optional category/price gating.
    cat_priority: dict from compute_category_priority or custom map
    """
    base = str(base_sku)
    sup_base = item_count.get(base, 0)
    if sup_base < min_support:
        return pd.DataFrame(columns=[
            "StockCode", "Description", "Category",
            "Confidence", "Lift", "Count", "Interpretation"
        ])

    N = df["InvoiceNo"].nunique()
    rows = []
    for (a, b), c in pair_count.items():
        if a != base or c < min_support:
            continue
        sup_b = item_count.get(b, 0)
        if sup_b == 0:
            continue
        conf = c / sup_base
        if conf < min_conf:
            continue
        lift = conf / (sup_b / N)
        rows.append((b, conf, lift, c, _interpret(conf, lift)))

    recs = (pd.DataFrame(rows, columns=[id_col, "Confidence", "Lift", "Count", "Interpretation"])
              .sort_values(["Confidence", "Lift", "Count"], ascending=False)
              .head(top_n * 3))

    if recs.empty:
        return recs

    meta_cols = [id_col, desc_col, cat_col]
    if price_col in df.columns:
        meta_cols.append(price_col)
    meta = df[meta_cols].drop_duplicates(subset=id_col)
    recs = recs.merge(meta, on=id_col, how="left")

    base_meta = meta.loc[meta[id_col] == base]
    if base_meta.empty:
        return recs.head(top_n)

    base_cat = base_meta[cat_col].iloc[0]
    base_price = base_meta[price_col].iloc[0] if price_col in base_meta.columns else None

    if cat_priority:
        base_rank = cat_priority.get(base_cat, float("inf"))
        recs = recs[recs[cat_col].map(lambda c: cat_priority.get(c, float("inf"))) <= base_rank]

    if enforce_price and base_price is not None:
        recs = recs[recs[price_col] <= base_price]

    recs = recs.head(top_n).rename(columns={
        id_col: "StockCode",
        desc_col: "Description",
        cat_col: "Category"
    }).reset_index(drop=True)

    keep_cols = ["StockCode", "Description", "Category", "Confidence", "Lift", "Count", "Interpretation"]
    return recs[[c for c in keep_cols if c in recs.columns]]
