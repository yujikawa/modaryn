select
    order_id || '-SHIP' as shipping_id,
    order_id,
    'Shipped' as shipping_status,
    '2023-01-05'::date as shipping_date
from {{ ref('stg_orders') }}
limit 5 -- Just for sample data
