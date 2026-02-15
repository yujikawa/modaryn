with expense_data as (
    select date('2023-01-01') as date_day, 'Rent' as expense_type, 1000.00 as amount
    union all
    select date('2023-01-01'), 'Utilities', 200.00
    union all
    select date('2023-01-02'), 'Rent', 1000.00
    union all
    select date('2023-01-02'), 'Marketing', 500.00
    union all
    select date('2023-01-03'), 'Utilities', 250.00
)

select *
from expense_data
