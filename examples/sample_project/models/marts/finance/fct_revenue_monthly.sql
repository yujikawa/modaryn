with monthly as (
    select * from {{ ref('int_monthly_revenue') }}
),
channels as (
    select * from {{ ref('dim_channels') }}
),
revenue_with_prev as (
    select
        m.revenue_month,
        m.channel,
        m.order_count,
        m.monthly_revenue,
        m.monthly_profit,
        m.profit_margin_pct,
        m.avg_order_value,
        m.cumulative_revenue,
        lag(m.monthly_revenue) over (
            partition by m.channel order by m.revenue_month
        ) as prev_month_revenue,
        c.channel_type,
        c.is_paid
    from monthly m
    left join channels c on m.channel = c.channel_name
)
select
    revenue_month,
    channel,
    channel_type,
    is_paid,
    order_count,
    monthly_revenue,
    monthly_profit,
    profit_margin_pct,
    avg_order_value,
    cumulative_revenue,
    prev_month_revenue,
    case
        when prev_month_revenue is null or prev_month_revenue = 0 then null
        else round((monthly_revenue - prev_month_revenue) / prev_month_revenue * 100, 2)
    end as revenue_growth_pct
from revenue_with_prev
