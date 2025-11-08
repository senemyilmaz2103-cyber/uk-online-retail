WITH source AS (
    SELECT * FROM {{ source('raw', 'online_retail') }}
),

renamed AS (
    SELECT
        CAST(InvoiceNo AS STRING) AS InvoiceNo,
        CAST(StockCode AS STRING) AS StockCode,
        Description,
        Quantity,
        InvoiceDate,
        SAFE_CAST(UnitPrice AS FLOAT64) AS UnitPrice,
        SAFE_CAST(CustomerID AS STRING) AS CustomerID,
        Country,

    FROM source
   
)

SELECT * FROM renamed