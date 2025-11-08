

WITH customer_summary AS (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS Frequency,
        SUM(TotalPrice) AS Monetary,
        MAX(InvoiceDate) AS LastPurchaseDate
    FROM {{ ref('int_online_retail') }}
    WHERE IsReturn = FALSE
    GROUP BY CustomerID
)

SELECT
    CustomerID,
    Frequency,
    ROUND(Monetary, 2) AS Monetary,
    LastPurchaseDate,
    DATE_DIFF(DATE('2011-12-31'), DATE(LastPurchaseDate), DAY) AS Recency
FROM customer_summary
