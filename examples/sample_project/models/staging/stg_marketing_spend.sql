select
    spend_id,
    campaign_id,
    channel,
    spend_date::date as spend_date,
    spend_amount,
    impressions,
    clicks,
    conversions,
    case
        when impressions > 0 then round(clicks::decimal / impressions * 100, 4)
        else 0
    end as click_through_rate,
    case
        when clicks > 0 then round(conversions::decimal / clicks * 100, 4)
        else 0
    end as conversion_rate
from {{ source('main', 'raw_marketing_spend') }}
