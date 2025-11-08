"""
Utility script to generate additional insight tables for BI consumption:
1. Category flow matrix: Base_Category -> Rec_Category aggregations.
2. Attachment funnel metrics per SKU.
3. Customer segment overlay for top bundle bases.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from recommender_directional import build_directional_pairs

DATA_PATH = Path("data/full_features_raw.csv")
TOP_PAIRS_PATH = Path("data/top_pairs_with_lift.csv")
RFM_PATH = Path("data/rfm_kmeans_results.csv")
CATEGORY_FLOW_PATH = Path("data/category_flow_matrix.csv")
ATTACHMENT_PATH = Path("data/attachment_metrics.csv")
SEGMENT_OVERLAY_PATH = Path("data/base_segment_overlay.csv")


def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df[df["Quantity"] > 0].copy()
    df["StockCode"] = df["StockCode"].astype(str)
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    return df


def export_category_flow(top_pairs: pd.DataFrame) -> None:
    filtered = top_pairs[
        (top_pairs["Base_Category"] != "Other") & (top_pairs["Rec_Category"] != "Other")
    ]
    flow = (
        filtered.groupby(["Base_Category", "Rec_Category"])
        .agg(
            pair_records=("Base", "count"),
            total_pair_count=("Count", "sum"),
            avg_confidence=("Confidence", "mean"),
            avg_lift=("Lift", "mean"),
        )
        .reset_index()
        .sort_values("total_pair_count", ascending=False)
    )
    flow.to_csv(CATEGORY_FLOW_PATH, index=False)


def export_attachment_metrics(df: pd.DataFrame, pair_count: dict[tuple[str, str], int]) -> None:
    min_support = 3
    rec_map: dict[str, set[str]] = defaultdict(set)
    for (base, rec), count in pair_count.items():
        if count >= min_support:
            rec_map[base].add(rec)

    baskets = (
        df.groupby("InvoiceNo")["StockCode"]
        .apply(lambda s: list(dict.fromkeys(s)))
    )

    base_totals: dict[str, int] = defaultdict(int)
    attach_totals: dict[str, int] = defaultdict(int)

    for items in baskets:
        item_set = set(items)
        for sku in item_set:
            base_totals[sku] += 1
            recs = rec_map.get(sku)
            if not recs:
                continue
            if item_set.intersection(recs):
                attach_totals[sku] += 1

    meta = (
        df[["StockCode", "Description", "category", "UnitPrice"]]
        .drop_duplicates(subset="StockCode")
        .rename(columns={"category": "Category"})
    )

    rows = []
    for sku, total in base_totals.items():
        if total < min_support:
            continue
        hits = attach_totals.get(sku, 0)
        rows.append(
            {
                "StockCode": sku,
                "TotalInvoices": total,
                "InvoicesWithRecommended": hits,
                "AttachmentRate": hits / total if total else 0.0,
            }
        )

    attachment_df = pd.DataFrame(rows)
    if attachment_df.empty:
        attachment_df = pd.DataFrame(
            columns=[
                "StockCode",
                "TotalInvoices",
                "InvoicesWithRecommended",
                "AttachmentRate",
            ]
        )

    attachment_df = (
        attachment_df.merge(meta, on="StockCode", how="left")
        .sort_values("AttachmentRate", ascending=False)
    )
    attachment_df.to_csv(ATTACHMENT_PATH, index=False)


def export_segment_overlay(df: pd.DataFrame, top_pairs: pd.DataFrame) -> None:
    if not RFM_PATH.exists():
        return

    rfm = pd.read_csv(RFM_PATH)[["CustomerID", "Segment"]]
    segment_df = df.merge(rfm, on="CustomerID", how="inner")

    base_skus = top_pairs["Base"].unique()
    subset = segment_df[segment_df["StockCode"].isin(base_skus)]
    if subset.empty:
        pd.DataFrame(
            columns=[
                "StockCode",
                "Description",
                "Segment",
                "CustomerCount",
                "InvoiceCount",
                "TotalQuantity",
                "TotalRevenue",
                "SegmentShare",
            ]
        ).to_csv(SEGMENT_OVERLAY_PATH, index=False)
        return

    overlay = (
        subset.groupby(["StockCode", "Description", "Segment"])
        .agg(
            CustomerCount=("CustomerID", "nunique"),
            InvoiceCount=("InvoiceNo", "nunique"),
            TotalQuantity=("Quantity", "sum"),
            TotalRevenue=("TotalPrice", "sum"),
        )
        .reset_index()
    )
    overlay["SegmentShare"] = (
        overlay.groupby("StockCode")["CustomerCount"]
        .transform(lambda x: x / x.sum())
    )

    overlay.sort_values(["StockCode", "SegmentShare"], ascending=[True, False]).to_csv(
        SEGMENT_OVERLAY_PATH, index=False
    )


def main() -> None:
    df = load_transactions()
    top_pairs = pd.read_csv(TOP_PAIRS_PATH)
    item_count, pair_count = build_directional_pairs(df)

    export_category_flow(top_pairs)
    export_attachment_metrics(df, pair_count)
    export_segment_overlay(df, top_pairs)
    print("Generated category_flow_matrix.csv, attachment_metrics.csv, base_segment_overlay.csv")


if __name__ == "__main__":
    main()
