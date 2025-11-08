

SELECT
    InvoiceNo,
    StockCode,
    Description,
    Quantity,
    InvoiceDate,
    ROUND(UnitPrice, 2) AS UnitPrice,
    COALESCE(CustomerID, 'Guest') AS CustomerID,
    Country,
    CASE 
        WHEN LEFT(InvoiceNo, 1) = 'C' OR Quantity < 0 THEN TRUE
        ELSE FALSE
    END AS IsReturn,
    ROUND(Quantity * UnitPrice, 2) AS TotalPrice,
    EXTRACT(YEAR FROM InvoiceDate) AS InvoiceYear,
    EXTRACT(MONTH FROM InvoiceDate) AS InvoiceMonth,
    EXTRACT(DAY FROM InvoiceDate) AS InvoiceDay,
    EXTRACT(WEEK FROM InvoiceDate) AS InvoiceWeek,
    EXTRACT(DAYOFWEEK FROM InvoiceDate) AS InvoiceDayOfWeek,
    
    -- Günün bölümü
    CASE 
        WHEN EXTRACT(HOUR FROM InvoiceDate) BETWEEN 0 AND 5 THEN 'Night'
        WHEN EXTRACT(HOUR FROM InvoiceDate) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN EXTRACT(HOUR FROM InvoiceDate) BETWEEN 12 AND 17 THEN 'Afternoon'
        ELSE 'Evening'
    END AS DayPart,

    -- Hafta içi / hafta sonu
    CASE 
        WHEN EXTRACT(DAYOFWEEK FROM InvoiceDate) IN (2,3,4,5,6) THEN 'Weekday'
        ELSE 'Weekend'
    END AS DayType

from {{ ref("stg_raw__online_retail") }} 
WHERE Quantity IS NOT NULL
  AND UnitPrice > 0
