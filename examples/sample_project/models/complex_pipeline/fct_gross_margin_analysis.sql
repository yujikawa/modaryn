with product_sales_with_costs as (
    select
        ft.transaction_id,
        ft.product_id,
        ft.amount as sales_revenue,
        ipc.unit_cost,
        ft.quantity,
        (ft.quantity * ipc.unit_cost) as total_cost
    from {{ ref('fct_customer_transactions') }} ft
    left join {{ ref('int_product_costs') }} ipc on ft.product_id = ipc.product_id
),
gross_margin as (
    select
        transaction_id,
        sales_revenue,
        total_cost,
        (sales_revenue - total_cost) as gross_margin
    from product_sales_with_costs
)

select *
from gross_margin
