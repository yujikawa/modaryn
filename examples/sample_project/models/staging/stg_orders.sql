select
    order_id,
    customer_id,
    order_date::date as order_date,
    status,
    channel,
    coalesce(coupon_code, 'NONE') as coupon_code,
    shipping_country
from {{ source('main', 'raw_orders') }}
