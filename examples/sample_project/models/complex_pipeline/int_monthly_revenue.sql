with monthly_sales as (
    select
        date_trunc('month', date_day) as date_month,
        sum(daily_revenue) as monthly_revenue
    from {{ ref('int_daily_sales') }}
    group by 1
)

select *
from monthly_sales
