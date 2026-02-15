with daily_orders as (
    select
        date_trunc('day', order_date) as date_day,
        sum(order_total) as daily_revenue
    from {{ ref('stg_orders') }}
    group by 1
)

select *
from daily_orders
