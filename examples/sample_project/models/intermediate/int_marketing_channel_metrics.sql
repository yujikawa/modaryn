with spend as (
    select
        channel,
        date_trunc('month', spend_date)::date as spend_month,
        sum(spend_amount) as total_spend,
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(conversions) as total_conversions
    from {{ ref('stg_marketing_spend') }}
    group by channel, date_trunc('month', spend_date)::date
),
revenue as (
    select
        channel,
        date_trunc('month', revenue_month)::date as revenue_month,
        sum(monthly_revenue) as attributed_revenue
    from {{ ref('int_monthly_revenue') }}
    group by channel, date_trunc('month', revenue_month)::date
)
select
    s.channel,
    s.spend_month,
    s.total_spend,
    s.total_impressions,
    s.total_clicks,
    s.total_conversions,
    coalesce(r.attributed_revenue, 0) as attributed_revenue,
    case
        when s.total_spend > 0 then round((coalesce(r.attributed_revenue, 0) - s.total_spend) / s.total_spend * 100, 2)
        else null
    end as roi_pct,
    case
        when s.total_conversions > 0 then round(s.total_spend / s.total_conversions, 2)
        else null
    end as cost_per_conversion
from spend s
left join revenue r
    on s.channel = r.channel
    and s.spend_month = r.revenue_month
