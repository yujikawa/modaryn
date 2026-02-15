with monthly_customer_base as (
    select
        date_trunc('month', order_date) as cohort_date,
        customer_id
    from {{ ref('stg_orders') }}
    group by 1, 2
),
retained_customers as (
    select
        c1.cohort_date,
        count(distinct c2.customer_id) as retained_customers_count,
        count(distinct c1.customer_id) as total_cohort_customers
    from monthly_customer_base c1
    left join monthly_customer_base c2
        on c1.customer_id = c2.customer_id
        and date_trunc('month', c2.cohort_date) = date_trunc('month', date_add(c1.cohort_date, interval '1' month))
    group by 1
)

select
    cohort_date,
    retained_customers_count,
    total_cohort_customers,
    (retained_customers_count * 1.0 / total_cohort_customers) as retention_rate
from retained_customers
