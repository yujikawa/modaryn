with order_channel as (
    select
        order_id,
        case (order_id % 3)
            when 0 then 'Organic Search'
            when 1 then 'Paid Search'
            else 'Social Media'
        end as attributed_channel,
        order_total as attributed_revenue
    from {{ ref('stg_orders') }}
)

select *
from order_channel
