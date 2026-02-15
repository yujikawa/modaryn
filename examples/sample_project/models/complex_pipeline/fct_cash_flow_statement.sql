with operating_activities as (
    select
        period,
        sum(total_revenue) as cash_in_from_sales,
        sum(total_expenses) as cash_out_for_expenses
    from {{ ref('fct_profit_and_loss_statement') }}
    group by 1
),
cash_flow as (
    select
        period,
        (cash_in_from_sales - cash_out_for_expenses) as operating_cash_flow,
        -- Dummy investing and financing cash flow for demonstration
        1000.00 as investing_cash_flow,
        500.00 as financing_cash_flow
    from operating_activities
)

select
    period,
    operating_cash_flow,
    operating_cash_flow + investing_cash_flow + financing_cash_flow as net_cash_flow
from cash_flow
