with daily as (
    select * from {{ ref('int_daily_revenue') }}
),
monthly_agg as (
    select
        date_trunc('month', order_date)::date as revenue_month,
        channel,
        sum(order_count) as order_count,
        sum(daily_revenue) as monthly_revenue,
        sum(daily_profit) as monthly_profit,
        avg(avg_order_value) as avg_order_value
    from daily
    group by date_trunc('month', order_date)::date, channel
)
select
    revenue_month,
    channel,
    order_count,
    monthly_revenue,
    monthly_profit,
    round(monthly_profit / nullif(monthly_revenue, 0) * 100, 2) as profit_margin_pct,
    avg_order_value,
    sum(monthly_revenue) over (
        partition by channel
        order by revenue_month
        rows between unbounded preceding and current row
    ) as cumulative_revenue
from monthly_agg
