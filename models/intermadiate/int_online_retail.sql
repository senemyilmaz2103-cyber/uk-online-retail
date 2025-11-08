

SELECT
    InvoiceNo,
    StockCode,
    Description,
    Quantity,
    InvoiceDate,
    ROUND(UnitPrice, 2) AS UnitPrice,
    
    -- CustomerID olmayanları Guest olarak işaretle
    COALESCE(CustomerID, 'Guest') AS CustomerID,
    Country,

    -- İade (return) işlemlerini belirleme
    CASE 
        WHEN LEFT(InvoiceNo, 1) = 'C' OR Quantity < 0 THEN TRUE
        ELSE FALSE
    END AS IsReturn,

    -- Toplam fiyatı hesapla ve yuvarla
    ROUND(Quantity * UnitPrice, 2) AS TotalPrice,

    -- Tarih özellikleri ekleme
    EXTRACT(YEAR FROM InvoiceDate) AS InvoiceYear,
    EXTRACT(MONTH FROM InvoiceDate) AS InvoiceMonth,
    EXTRACT(DAY FROM InvoiceDate) AS InvoiceDay,
    EXTRACT(WEEK FROM InvoiceDate) AS InvoiceWeek,
    EXTRACT(DAYOFWEEK FROM InvoiceDate) AS InvoiceDayOfWeek

from {{ ref("stg_raw__online_retail") }} 
WHERE Quantity IS NOT NULL
  AND UnitPrice > 0
