with channel_metrics as (
    select * from {{ ref('int_marketing_channel_metrics') }}
),
channels as (
    select * from {{ ref('dim_channels') }}
),
monthly_totals as (
    select
        spend_month,
        sum(total_spend) as total_monthly_spend,
        sum(attributed_revenue) as total_monthly_revenue
    from channel_metrics
    group by spend_month
)
select
    cm.channel,
    cm.spend_month,
    ch.channel_type,
    ch.is_paid,
    cm.total_spend,
    cm.total_impressions,
    cm.total_clicks,
    cm.total_conversions,
    cm.attributed_revenue,
    cm.roi_pct,
    cm.cost_per_conversion,
    mt.total_monthly_spend,
    mt.total_monthly_revenue,
    case
        when mt.total_monthly_spend > 0
        then round(cm.total_spend / mt.total_monthly_spend * 100, 2)
        else 0
    end as spend_share_pct,
    case
        when cm.roi_pct >= 300 then 'excellent'
        when cm.roi_pct >= 100 then 'good'
        when cm.roi_pct >= 0 then 'break_even'
        when cm.roi_pct is null then 'organic'
        else 'negative_roi'
    end as roi_tier
from channel_metrics cm
left join channels ch on cm.channel = ch.channel_name
left join monthly_totals mt
    on cm.spend_month = mt.spend_month
