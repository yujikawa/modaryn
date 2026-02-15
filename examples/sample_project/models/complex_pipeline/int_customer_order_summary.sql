with customer_orders as (
    select
        s_o.customer_id,
        count(distinct s_o.order_id) as total_orders,
        sum(s_o.quantity * s_p.price) as total_spend,
        min(s_o.order_date) as first_order_date,
        max(s_o.order_date) as most_recent_order_date
    from {{ ref('stg_orders') }} as s_o
    join {{ ref('stg_products') }} as s_p
        on s_o.product_id = s_p.product_id
    group by
        s_o.customer_id
),
customer_summary as (
    select
        s_c.customer_id,
        s_c.customer_name,
        s_c.customer_segment,
        co.total_orders,
        co.total_spend,
        co.first_order_date,
        co.most_recent_order_date,
        case
            when co.total_spend >= 1000 and s_c.customer_segment = 'Premium' then 'High Value Premium'
            when co.total_spend >= 500 then 'High Value Standard'
            else 'Low Value'
        end as customer_value_segment
    from {{ ref('stg_customers') }} as s_c
    left join customer_orders as co
        on s_c.customer_id = co.customer_id
)
select * from customer_summary