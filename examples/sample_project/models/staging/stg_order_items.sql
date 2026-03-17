select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount_pct,
    round(unit_price * quantity * (1 - discount_pct), 2) as line_total
from {{ source('main', 'raw_order_items') }}
