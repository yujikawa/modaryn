with product_sales as (
    select
        product_id,
        date_trunc('day', order_date) as date_day,
        sum(quantity) as daily_quantity_sold,
        sum(order_total) as daily_sales
    from {{ ref('stg_orders') }}
    group by 1, 2
)

select *
from product_sales
