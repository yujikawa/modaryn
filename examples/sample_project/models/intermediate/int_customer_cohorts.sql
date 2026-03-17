with customers as (
    select customer_id, signup_date
    from {{ ref('stg_customers') }}
),
first_orders as (
    select
        customer_id,
        min(order_date) as first_order_date
    from {{ ref('stg_orders') }}
    where status = 'completed'
    group by customer_id
),
cohort_assignment as (
    select
        c.customer_id,
        c.signup_date,
        fo.first_order_date,
        date_trunc('month', fo.first_order_date)::date as cohort_month,
        fo.first_order_date - c.signup_date as days_to_first_order
    from customers c
    left join first_orders fo on c.customer_id = fo.customer_id
)
select
    customer_id,
    signup_date,
    first_order_date,
    cohort_month,
    days_to_first_order,
    case
        when first_order_date is null then 'never_converted'
        when days_to_first_order <= 7 then 'fast_converter'
        when days_to_first_order <= 30 then 'normal_converter'
        else 'slow_converter'
    end as conversion_type
from cohort_assignment
