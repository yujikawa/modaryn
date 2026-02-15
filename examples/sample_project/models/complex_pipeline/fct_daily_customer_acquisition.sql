with customer_first_order as (
    select
        customer_id,
        min(order_date) as first_order_date
    from {{ ref('stg_orders') }}
    group by customer_id
)

select
    date_trunc('day', first_order_date) as date_day,
    count(distinct customer_id) as new_customers
from customer_first_order
group by 1
