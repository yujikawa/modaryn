with order_shipping as (
    select
        o.order_id,
        s.shipping_status,
        s.shipping_date
    from {{ ref('stg_orders') }} o
    left join {{ ref('stg_shipping') }} s on o.order_id = s.order_id
)

select *
from order_shipping
