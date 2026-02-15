select
    order_id,
    customer_id,
    product_id,
    quantity,
    order_date
from {{ source('sample_project', 'orders') }}