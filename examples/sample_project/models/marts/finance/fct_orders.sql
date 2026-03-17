with orders as (
    select * from {{ ref('int_order_profitability') }}
),
customers as (
    select customer_id, segment, country
    from {{ ref('dim_customers') }}
),
dates as (
    select date_day, month_name, quarter, is_weekend
    from {{ ref('dim_dates') }}
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
    o.refund_amount,
    o.net_revenue,
    o.profitability_tier,
    c.segment as customer_segment,
    c.country,
    d.month_name,
    d.quarter,
    d.is_weekend
from orders o
left join customers c on o.customer_id = c.customer_id
left join dates d on o.order_date = d.date_day
