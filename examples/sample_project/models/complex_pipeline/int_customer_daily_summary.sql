with customer_orders as (
    select
        customer_id,
        date_trunc('day', order_date) as date_day,
        sum(order_total) as daily_spend
    from {{ ref('stg_orders') }}
    group by 1, 2
)

select *
from customer_orders
