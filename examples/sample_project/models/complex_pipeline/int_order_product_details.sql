with order_details as (
    select
        s_o.order_id,
        s_o.customer_id,
        s_o.product_id,
        s_o.quantity,
        s_p.product_name,
        s_p.price,
        (s_o.quantity * s_p.price) as line_item_total
    from {{ ref('stg_orders') }} as s_o
    join {{ ref('stg_products') }} as s_p
        on s_o.product_id = s_p.product_id
)
select * from order_details