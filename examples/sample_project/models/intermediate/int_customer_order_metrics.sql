with completed_orders as (
    select *
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'
),
order_metrics as (
    select
        customer_id,
        count(order_id) as total_orders,
        sum(order_revenue) as total_revenue,
        avg(order_revenue) as avg_order_value,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        sum(order_profit) as total_profit,
        count(distinct channel) as channels_used
    from completed_orders
    group by customer_id
),
order_frequency as (
    select
        customer_id,
        total_orders,
        first_order_date,
        last_order_date,
        case
            when total_orders = 1 then 'one_time'
            when total_orders between 2 and 4 then 'repeat'
            when total_orders between 5 and 9 then 'loyal'
            else 'champion'
        end as frequency_segment,
        case
            when last_order_date >= current_date - interval '30 days' then 1
            when last_order_date >= current_date - interval '90 days' then 2
            when last_order_date >= current_date - interval '180 days' then 3
            else 4
        end as recency_score
    from order_metrics
)
select
    m.customer_id,
    m.total_orders,
    m.total_revenue,
    m.avg_order_value,
    m.first_order_date,
    m.last_order_date,
    m.total_profit,
    m.channels_used,
    f.frequency_segment,
    f.recency_score,
    current_date - m.last_order_date as days_since_last_order
from order_metrics m
join order_frequency f on m.customer_id = f.customer_id
