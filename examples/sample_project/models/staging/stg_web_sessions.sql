select
    session_id,
    customer_id,
    session_date::date as session_date,
    channel,
    device_type,
    pages_viewed,
    session_duration_sec,
    bounced::boolean as bounced,
    converted::boolean as converted,
    case
        when session_duration_sec >= 300 then 'engaged'
        when session_duration_sec >= 60 then 'browsing'
        else 'quick'
    end as engagement_level
from {{ source('main', 'raw_web_sessions') }}
