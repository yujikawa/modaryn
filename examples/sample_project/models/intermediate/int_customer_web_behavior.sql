with sessions as (
    select * from {{ ref('stg_web_sessions') }}
),
session_aggregates as (
    select
        customer_id,
        count(session_id) as total_sessions,
        sum(pages_viewed) as total_pages_viewed,
        avg(pages_viewed) as avg_pages_per_session,
        avg(session_duration_sec) as avg_session_duration_sec,
        sum(case when bounced then 1 else 0 end) as bounce_count,
        sum(case when converted then 1 else 0 end) as conversion_sessions,
        count(distinct channel) as channels_visited,
        min(session_date) as first_session_date,
        max(session_date) as last_session_date
    from sessions
    group by customer_id
)
select
    customer_id,
    total_sessions,
    total_pages_viewed,
    round(avg_pages_per_session, 2) as avg_pages_per_session,
    round(avg_session_duration_sec, 0) as avg_session_duration_sec,
    bounce_count,
    conversion_sessions,
    channels_visited,
    first_session_date,
    last_session_date,
    round(bounce_count::decimal / nullif(total_sessions, 0) * 100, 2) as bounce_rate_pct,
    round(conversion_sessions::decimal / nullif(total_sessions, 0) * 100, 2) as session_conversion_rate_pct
from session_aggregates
