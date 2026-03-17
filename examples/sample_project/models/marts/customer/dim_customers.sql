with customers as (
    select * from {{ ref('stg_customers') }}
),
order_metrics as (
    select * from {{ ref('int_customer_order_metrics') }}
),
cohorts as (
    select * from {{ ref('int_customer_cohorts') }}
)
select
    c.customer_id,
    c.customer_name,
    c.email,
    c.signup_date,
    c.country,
    c.city,
    c.segment,
    c.age_group,
    c.referral_source,
    coalesce(om.total_orders, 0) as total_orders,
    coalesce(om.total_revenue, 0.0) as total_revenue,
    om.first_order_date,
    om.last_order_date,
    om.frequency_segment,
    cohorts.cohort_month,
    cohorts.conversion_type,
    case
        when om.customer_id is null then 'prospect'
        when om.last_order_date >= current_date - interval '90 days' then 'active'
        when om.last_order_date >= current_date - interval '180 days' then 'at_risk'
        else 'lapsed'
    end as customer_status
from customers c
left join order_metrics om on c.customer_id = om.customer_id
left join cohorts on c.customer_id = cohorts.customer_id
