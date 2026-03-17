with customer_metrics as (
    select * from {{ ref('int_customer_order_metrics') }}
),
web_behavior as (
    select * from {{ ref('int_customer_web_behavior') }}
),
customers as (
    select * from {{ ref('dim_customers') }}
),
ltv_components as (
    select
        cm.customer_id,
        cm.total_revenue,
        cm.total_orders,
        cm.avg_order_value,
        cm.total_profit,
        cm.first_order_date,
        cm.last_order_date,
        cm.days_since_last_order,
        cm.recency_score,
        coalesce(wb.total_sessions, 0) as total_sessions,
        coalesce(wb.session_conversion_rate_pct, 0) as session_conversion_rate
    from customer_metrics cm
    left join web_behavior wb on cm.customer_id = wb.customer_id
),
ltv_scored as (
    select
        customer_id,
        total_revenue,
        total_orders,
        avg_order_value,
        total_profit,
        first_order_date,
        last_order_date,
        days_since_last_order,
        recency_score,
        total_sessions,
        session_conversion_rate,
        -- Projected next 12-month LTV based on recency and frequency
        avg_order_value * total_orders / greatest(
            (last_order_date - first_order_date) / 365.0, 0.1
        ) * case
            when recency_score = 1 then 12.0
            when recency_score = 2 then 8.0
            when recency_score = 3 then 3.0
            else 0.5
        end as projected_annual_revenue,
        case
            when total_revenue >= 3000 and total_orders >= 8 then 'champion'
            when total_revenue >= 1500 and total_orders >= 4 then 'loyal'
            when total_revenue >= 500 and total_orders >= 2 then 'promising'
            when recency_score <= 2 then 'new_customer'
            else 'at_risk'
        end as ltv_segment
    from ltv_components
)
select
    ls.customer_id,
    c.customer_name,
    c.segment,
    c.country,
    c.cohort_month,
    ls.total_revenue,
    ls.total_orders,
    ls.avg_order_value,
    ls.total_profit,
    ls.first_order_date,
    ls.last_order_date,
    ls.days_since_last_order,
    ls.total_sessions,
    ls.session_conversion_rate,
    round(ls.projected_annual_revenue, 2) as projected_annual_revenue,
    ls.ltv_segment
from ltv_scored ls
join customers c on ls.customer_id = c.customer_id
