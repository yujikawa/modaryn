with monthly_revenue as (
    select
        date_month as period,
        monthly_revenue as total_revenue
    from {{ ref('int_monthly_revenue') }}
),
monthly_expenses as (
    -- Dummy expenses for demonstration, replace with actual expense data
    select
        date_trunc('month', date_day) as period,
        sum(daily_revenue * 0.4) as total_expenses -- Assume 40% of revenue as expenses
    from {{ ref('int_daily_sales') }}
    group by 1
),
pnl as (
    select
        rev.period,
        rev.total_revenue,
        exp.total_expenses,
        rev.total_revenue - exp.total_expenses as net_profit
    from monthly_revenue rev
    left join monthly_expenses exp on rev.period = exp.period
)

select *
from pnl
