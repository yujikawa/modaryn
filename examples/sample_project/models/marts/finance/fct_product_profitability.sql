with product_metrics as (
    select * from {{ ref('int_product_sales_metrics') }}
),
returns as (
    select
        oi.product_id,
        count(r.return_id) as return_count,
        sum(r.refund_amount) as total_refunded
    from {{ ref('stg_order_items') }} oi
    join {{ ref('stg_returns') }} r on oi.order_item_id = r.order_item_id
    group by oi.product_id
)
select
    pm.product_id,
    pm.product_name,
    pm.category,
    pm.brand,
    pm.list_price,
    pm.cost_price,
    pm.times_ordered,
    pm.total_units_sold,
    pm.total_revenue,
    pm.total_cost,
    pm.total_profit,
    pm.achieved_margin_pct,
    coalesce(r.return_count, 0) as return_count,
    coalesce(r.total_refunded, 0) as total_refunded,
    pm.total_revenue - coalesce(r.total_refunded, 0) as net_revenue,
    case
        when pm.achieved_margin_pct >= 40 then 'high_margin'
        when pm.achieved_margin_pct >= 25 then 'normal_margin'
        when pm.achieved_margin_pct >= 10 then 'low_margin'
        else 'loss_making'
    end as margin_tier
from product_metrics pm
left join returns r on pm.product_id = r.product_id
