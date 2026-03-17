with completed_orders as (
    select
        order_date,
        channel,
        order_revenue,
        order_profit
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'
)
select
    order_date,
    channel,
    count(*) as order_count,
    sum(order_revenue) as daily_revenue,
    sum(order_profit) as daily_profit,
    avg(order_revenue) as avg_order_value
from completed_orders
group by order_date, channel
