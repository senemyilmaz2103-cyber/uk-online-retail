SELECT
    InvoiceYear,
    InvoiceMonth,
    InvoiceWeek,
    InvoiceDayOfWeek,
    DayPart,
    DayType,
    round(SUM(TotalPrice),2) AS TotalRevenue,
    round(SUM(Quantity),2) AS TotalQuantity,
    COUNT(DISTINCT InvoiceNo) AS NumberOfInvoices
FROM {{ ref('int_online_retail') }}
WHERE IsReturn = FALSE
GROUP BY InvoiceYear, InvoiceMonth, InvoiceWeek, InvoiceDayOfWeek, DayPart, DayType
ORDER BY InvoiceYear, InvoiceMonth, InvoiceWeek
