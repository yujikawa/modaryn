select
    product_id,
    product_name,
    price
from {{ source('sample_project', 'products') }}