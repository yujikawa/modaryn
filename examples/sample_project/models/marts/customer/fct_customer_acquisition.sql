with cohorts as (
    select * from {{ ref('int_customer_cohorts') }}
),
customers as (
    select customer_id, referral_source, signup_date, country
    from {{ ref('stg_customers') }}
),
first_order_value as (
    select
        customer_id,
        order_revenue as first_order_revenue,
        channel as acquisition_channel
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'
    qualify row_number() over (partition by customer_id order by order_date asc) = 1
)
select
    c.customer_id,
    c.signup_date,
    c.country,
    c.referral_source,
    co.cohort_month,
    co.first_order_date,
    co.days_to_first_order,
    co.conversion_type,
    fov.first_order_revenue,
    fov.acquisition_channel
from customers c
left join cohorts co on c.customer_id = co.customer_id
left join first_order_value fov on c.customer_id = fov.customer_id
