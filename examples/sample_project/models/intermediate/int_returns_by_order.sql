with returns as (
    select * from {{ ref('stg_returns') }}
),
orders as (
    select order_id, customer_id, order_date, order_revenue
    from {{ ref('int_orders_enriched') }}
)
select
    r.return_id,
    r.order_id,
    r.order_item_id,
    r.return_date,
    r.reason,
    r.status,
    r.refund_amount,
    o.customer_id,
    o.order_date,
    o.order_revenue,
    r.return_date - o.order_date as days_to_return,
    case
        when r.status = 'approved' then true
        else false
    end as is_refunded
from returns r
join orders o on r.order_id = o.order_id
