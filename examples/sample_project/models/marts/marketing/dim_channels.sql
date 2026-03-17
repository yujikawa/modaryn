select
    channel_name,
    channel_type,
    is_paid,
    typical_cpc_range
from (values
    ('organic', 'organic_search', false, 'N/A'),
    ('paid_search', 'paid_search', true, '$0.50-$3.00'),
    ('social', 'social_media', true, '$0.20-$1.50'),
    ('email', 'email_marketing', false, 'N/A'),
    ('referral', 'referral', false, 'N/A'),
    ('display', 'display_advertising', true, '$0.10-$0.80'),
    ('influencer', 'influencer_marketing', true, 'variable'),
    ('affiliate', 'affiliate', true, 'variable'),
    ('mobile', 'mobile_app', false, 'N/A')
) as t(channel_name, channel_type, is_paid, typical_cpc_range)
