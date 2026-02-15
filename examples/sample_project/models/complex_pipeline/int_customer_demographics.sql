with customer_base as (
    select customer_id from {{ ref('stg_customers') }}
),
demographics as (
    select
        customer_id,
        case
            when customer_id % 3 = 0 then '18-24'
            when customer_id % 3 = 1 then '25-40'
            else '40+'
        end as age_group,
        case
            when customer_id % 2 = 0 then 'Male'
            else 'Female'
        end as gender
    from customer_base
)

select *
from demographics
