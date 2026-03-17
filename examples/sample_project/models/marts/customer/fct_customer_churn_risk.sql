with customer_metrics as (
    select * from {{ ref('int_customer_order_metrics') }}
),
web_behavior as (
    select * from {{ ref('int_customer_web_behavior') }}
),
order_data as (
    select
        customer_id,
        count(case when status = 'returned' then 1 end) as return_count,
        count(order_id) as total_orders_including_returns
    from {{ ref('stg_orders') }}
    group by customer_id
),
risk_signals as (
    select
        cm.customer_id,
        cm.days_since_last_order,
        cm.recency_score,
        cm.total_orders,
        cm.avg_order_value,
        coalesce(wb.bounce_rate_pct, 100) as bounce_rate_pct,
        coalesce(wb.total_sessions, 0) as total_sessions,
        coalesce(od.return_count, 0) as return_count,
        -- Recency risk: 0 (low) to 40 (high)
        case
            when cm.days_since_last_order <= 30 then 0
            when cm.days_since_last_order <= 60 then 10
            when cm.days_since_last_order <= 90 then 20
            when cm.days_since_last_order <= 180 then 30
            else 40
        end as recency_risk_score,
        -- Frequency risk: 0 (low) to 30 (high)
        case
            when cm.total_orders >= 8 then 0
            when cm.total_orders >= 5 then 10
            when cm.total_orders >= 3 then 20
            else 30
        end as frequency_risk_score,
        -- Engagement risk: 0 (low) to 30 (high)
        case
            when coalesce(wb.total_sessions, 0) >= 10 then 0
            when coalesce(wb.total_sessions, 0) >= 5 then 10
            when coalesce(wb.total_sessions, 0) >= 2 then 20
            else 30
        end as engagement_risk_score
    from customer_metrics cm
    left join web_behavior wb on cm.customer_id = wb.customer_id
    left join order_data od on cm.customer_id = od.customer_id
)
select
    customer_id,
    days_since_last_order,
    total_orders,
    avg_order_value,
    bounce_rate_pct,
    total_sessions,
    return_count,
    recency_risk_score,
    frequency_risk_score,
    engagement_risk_score,
    recency_risk_score + frequency_risk_score + engagement_risk_score as total_risk_score,
    case
        when recency_risk_score + frequency_risk_score + engagement_risk_score >= 70 then 'critical'
        when recency_risk_score + frequency_risk_score + engagement_risk_score >= 50 then 'high'
        when recency_risk_score + frequency_risk_score + engagement_risk_score >= 30 then 'medium'
        else 'low'
    end as churn_risk_tier
from risk_signals
