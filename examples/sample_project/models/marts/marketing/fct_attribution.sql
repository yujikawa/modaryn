with sessions as (
    select * from {{ ref('stg_web_sessions') }}
),
orders as (
    select
        order_id,
        customer_id,
        order_date,
        order_revenue,
        channel as order_channel
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'
),
customer_touchpoints as (
    select
        s.customer_id,
        s.session_date,
        s.channel,
        s.converted,
        o.order_id,
        o.order_revenue,
        o.order_date,
        row_number() over (partition by s.customer_id order by s.session_date asc) as touch_sequence,
        row_number() over (partition by s.customer_id order by s.session_date desc) as reverse_touch_sequence,
        count(*) over (partition by s.customer_id) as total_touches
    from sessions s
    left join orders o
        on s.customer_id = o.customer_id
        and s.session_date <= o.order_date
        and s.session_date >= o.order_date - interval '30 days'
),
attribution as (
    select
        customer_id,
        channel,
        session_date,
        order_id,
        order_revenue,
        total_touches,
        touch_sequence,
        -- First-touch attribution: 100% to first channel
        case when touch_sequence = 1 then order_revenue else 0 end as first_touch_revenue,
        -- Last-touch attribution: 100% to last channel
        case when reverse_touch_sequence = 1 then order_revenue else 0 end as last_touch_revenue,
        -- Linear attribution: equal split across all touches
        case when order_id is not null
            then round(order_revenue / nullif(total_touches, 0), 2)
            else 0
        end as linear_attributed_revenue
    from customer_touchpoints
)
select
    channel,
    count(distinct customer_id) as unique_customers,
    count(distinct order_id) as attributed_orders,
    sum(first_touch_revenue) as first_touch_revenue,
    sum(last_touch_revenue) as last_touch_revenue,
    sum(linear_attributed_revenue) as linear_attributed_revenue
from attribution
group by channel
