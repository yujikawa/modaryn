with customer_LTV as (
    select
        c.customer_id,
        sum(o.order_total) as lifetime_value
    from {{ ref('stg_customers') }} c
    join {{ ref('stg_orders') }} o on c.customer_id = o.customer_id
    group by c.customer_id
),
customer_order_frequency as (
    select
        customer_id,
        count(order_id) as order_count,
        count(distinct product_id) as distinct_products
    from {{ ref('stg_orders') }}
    group by customer_id
),
customer_segments as (
    select
        cltv.customer_id,
        cltv.lifetime_value,
        cof.order_count,
        cof.distinct_products,
        case
            when cltv.lifetime_value > 1000 and cof.order_count > 5 then 'High-Value Frequent'
            when cltv.lifetime_value > 500 and cof.order_count > 2 then 'Medium-Value Frequent'
            when cltv.lifetime_value > 200 then 'Low-Value Loyal'
            else 'New/Churned'
        end as segment
    from customer_LTV cltv
    join customer_order_frequency cof on cltv.customer_id = cof.customer_id
)

select *
from customer_segments
