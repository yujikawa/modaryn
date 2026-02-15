select
    product_id as product_key,
    product_name,
    case
        when product_id % 2 = 0 then 'Electronics'
        else 'Books'
    end as product_category
from {{ ref('stg_products') }}
