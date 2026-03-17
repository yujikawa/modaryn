select
    product_id,
    product_name,
    category,
    brand,
    cost_price,
    list_price,
    round(list_price - cost_price, 2) as gross_margin,
    round((list_price - cost_price) / list_price * 100, 2) as margin_pct,
    is_active::boolean as is_active
from {{ source('main', 'raw_products') }}
