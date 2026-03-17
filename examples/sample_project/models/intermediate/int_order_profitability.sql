with orders as (
    select * from {{ ref('int_orders_enriched') }}
),
returns as (
    select
        order_id,
        sum(refund_amount) as total_refunded
    from {{ ref('int_returns_by_order') }}
    where is_refunded
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    o.channel,
    o.order_revenue,
    o.order_profit,
    o.order_margin_pct,
    coalesce(r.total_refunded, 0) as refund_amount,
    o.order_revenue - coalesce(r.total_refunded, 0) as net_revenue,
    case
        when o.status = 'cancelled' then 'cancelled'
        when o.status = 'returned' then 'returned'
        when o.order_margin_pct >= 30 then 'high_margin'
        when o.order_margin_pct >= 15 then 'normal_margin'
        else 'low_margin'
    end as profitability_tier
from orders o
left join returns r on o.order_id = r.order_id
