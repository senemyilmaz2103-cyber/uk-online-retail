
SELECT
    StockCode,
    Description,
    SUM(Quantity) AS TotalQuantitySold,
    SUM(TotalPrice) AS TotalRevenue,
    SUM(CASE WHEN IsReturn THEN 1 ELSE 0 END) AS TotalReturns,
    ROUND(SUM(TotalPrice) / NULLIF(SUM(Quantity),0),2) AS AvgUnitPrice
FROM {{ ref('int_online_retail') }}
GROUP BY StockCode, Description
