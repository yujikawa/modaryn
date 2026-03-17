with order_items as (
    select * from {{ ref('stg_order_items') }}
),
completed_orders as (
    select order_id, order_date
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'
),
products as (
    select * from {{ ref('stg_products') }}
),
sales as (
    select
        oi.product_id,
        count(oi.order_item_id) as times_ordered,
        sum(oi.quantity) as total_units_sold,
        sum(oi.line_total) as total_revenue,
        avg(oi.unit_price) as avg_selling_price,
        sum(oi.quantity * p.cost_price) as total_cost,
        sum(oi.line_total - oi.quantity * p.cost_price) as total_profit,
        min(co.order_date) as first_sale_date,
        max(co.order_date) as last_sale_date
    from order_items oi
    join completed_orders co on oi.order_id = co.order_id
    join products p on oi.product_id = p.product_id
    group by oi.product_id
)
select
    s.product_id,
    p.product_name,
    p.category,
    p.brand,
    p.list_price,
    p.cost_price,
    s.times_ordered,
    s.total_units_sold,
    s.total_revenue,
    s.avg_selling_price,
    s.total_cost,
    s.total_profit,
    round(s.total_profit / nullif(s.total_revenue, 0) * 100, 2) as achieved_margin_pct,
    s.first_sale_date,
    s.last_sale_date
from sales s
join products p on s.product_id = p.product_id
