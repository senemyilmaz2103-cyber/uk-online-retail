import pandas as pd
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from recommender_directional import (
    build_directional_pairs,
    recommend_directional,
)

def test_recommend_directional_respects_priority_and_price():
    data = [
        # Invoice with a primary item plus two accessories (one overpriced)
        {"InvoiceNo": "1", "StockCode": "PHONE", "Description": "Smartphone",
         "Quantity": 1, "InvoiceDate": "2024-01-01 10:00:00", "UnitPrice": 500,
         "CustomerID": 1, "category": "Primary"},
        {"InvoiceNo": "1", "StockCode": "CASE", "Description": "Protective Case",
         "Quantity": 1, "InvoiceDate": "2024-01-01 10:00:00", "UnitPrice": 30,
         "CustomerID": 1, "category": "Accessory"},
        {"InvoiceNo": "1", "StockCode": "CHARGER", "Description": "Fast Charger",
         "Quantity": 1, "InvoiceDate": "2024-01-01 10:00:00", "UnitPrice": 25,
         "CustomerID": 1, "category": "Accessory"},
        {"InvoiceNo": "1", "StockCode": "LUXE_CASE", "Description": "Luxury Case",
         "Quantity": 1, "InvoiceDate": "2024-01-01 10:00:00", "UnitPrice": 800,
         "CustomerID": 1, "category": "Accessory"},

        # Reinforce real-world co-purchases
        {"InvoiceNo": "2", "StockCode": "PHONE", "Description": "Smartphone",
         "Quantity": 1, "InvoiceDate": "2024-01-02 11:00:00", "UnitPrice": 500,
         "CustomerID": 2, "category": "Primary"},
        {"InvoiceNo": "2", "StockCode": "CHARGER", "Description": "Fast Charger",
         "Quantity": 1, "InvoiceDate": "2024-01-02 11:00:00", "UnitPrice": 25,
         "CustomerID": 2, "category": "Accessory"},

        # Accessory-first basket to ensure we try to recommend “upwards”
        {"InvoiceNo": "3", "StockCode": "CASE", "Description": "Protective Case",
         "Quantity": 1, "InvoiceDate": "2024-01-03 12:00:00", "UnitPrice": 30,
         "CustomerID": 3, "category": "Accessory"},
        {"InvoiceNo": "3", "StockCode": "PHONE", "Description": "Smartphone",
         "Quantity": 1, "InvoiceDate": "2024-01-03 12:00:00", "UnitPrice": 500,
         "CustomerID": 3, "category": "Primary"},
    ]
    df = pd.DataFrame(data)

    item_count, pair_count = build_directional_pairs(df)

    # Higher number = “more primary”. This allows PHONE (2) to recommend accessories (1),
    # but not the other way around.
    cat_priority = {"Accessory": 1, "Primary": 2}

    phone_recs = recommend_directional(
        "PHONE",
        item_count,
        pair_count,
        df,
        top_n=5,
        min_support=1,
        min_conf=0.0,
        cat_priority=cat_priority,
        enforce_price=True,
    )
    assert set(phone_recs["StockCode"]) == {"CASE", "CHARGER"}
    assert "LUXE_CASE" not in phone_recs["StockCode"].values  # fails price gate

    case_recs = recommend_directional(
        "CASE",
        item_count,
        pair_count,
        df,
        top_n=5,
        min_support=1,
        min_conf=0.0,
        cat_priority=cat_priority,
        enforce_price=True,
    )
    # CASE sees PHONE in the raw counts, but cat priority + price should block it.
    assert "PHONE" not in case_recs["StockCode"].values
    charger_recs = recommend_directional(
        "CHARGER",
        item_count,
        pair_count,
        df,
        top_n=5,
        min_support=1,
        min_conf=0.0,
        cat_priority=cat_priority,
        enforce_price=True,
    )
    # CHARGER sees PHONE in the raw counts, but cat priority + price should block it.
    assert "PHONE" not in charger_recs["StockCode"].values