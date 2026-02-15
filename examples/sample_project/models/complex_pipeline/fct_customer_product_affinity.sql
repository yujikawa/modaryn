with customer_product_spend as (
    select
        cos.customer_id,
        cos.customer_name,
        opd.product_id,
        opd.product_name,
        sum(opd.line_item_total) as total_product_spend
    from {{ ref('int_customer_order_summary') }} as cos
    join {{ ref('int_order_product_details') }} as opd
        on cos.customer_id = opd.customer_id
    group by
        cos.customer_id,
        cos.customer_name,
        opd.product_id,
        opd.product_name
),
ranked_customer_products as (
    select
        customer_id,
        customer_name,
        product_id,
        product_name,
        total_product_spend,
        row_number() over (partition by customer_id order by total_product_spend desc) as rnk
    from customer_product_spend
    where total_product_spend > 0 -- Filter out customers who haven't spent anything
)
select
    customer_id,
    customer_name,
    product_id,
    product_name,
    total_product_spend
from ranked_customer_products
where rnk <= 3 -- Get top 3 products for each customer