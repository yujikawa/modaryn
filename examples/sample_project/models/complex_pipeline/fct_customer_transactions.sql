with transactions as (
    select
        order_id || '-' || product_id || '-' || customer_id as transaction_id, -- Simple unique ID
        order_id,
        customer_id,
        product_id,
        order_date as transaction_date,
        quantity,
        price,
        order_total as amount
    from {{ ref('stg_orders') }}
)

select *
from transactions
