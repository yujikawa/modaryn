with orders as (
    select * from {{ ref('stg_orders') }}
),
order_items as (
    select * from {{ ref('stg_order_items') }}
),
products as (
    select * from {{ ref('stg_products') }}
),
items_with_product as (
    select
        oi.order_item_id,
        oi.order_id,
        oi.product_id,
        oi.quantity,
        oi.unit_price,
        oi.discount_pct,
        oi.line_total,
        p.product_name,
        p.category,
        p.brand,
        p.cost_price,
        round(oi.line_total - (p.cost_price * oi.quantity), 2) as item_profit
    from order_items oi
    join products p on oi.product_id = p.product_id
),
order_totals as (
    select
        order_id,
        count(order_item_id) as item_count,
        sum(line_total) as order_revenue,
        sum(quantity) as total_quantity,
        sum(item_profit) as order_profit
    from items_with_product
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    o.channel,
    o.coupon_code,
    o.shipping_country,
    ot.item_count,
    ot.order_revenue,
    ot.total_quantity,
    ot.order_profit,
    round(ot.order_profit / nullif(ot.order_revenue, 0) * 100, 2) as order_margin_pct
from orders o
left join order_totals ot on o.order_id = ot.order_id
