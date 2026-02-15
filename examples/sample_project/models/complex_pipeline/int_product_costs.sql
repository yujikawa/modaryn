with product_base_costs as (
    select
        product_id,
        (row_number() over (order by product_id) * 10.0) as unit_cost
    from {{ ref('stg_products') }}
)

select *
from product_base_costs
