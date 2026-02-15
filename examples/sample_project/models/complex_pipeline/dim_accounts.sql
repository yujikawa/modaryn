select
    (row_number() over (order by 1)) as account_id,
    'Account ' || (row_number() over (order by 1)) as account_name
from (
    select 1 as x union all
    select 2 as x union all
    select 3 as x union all
    select 4 as x union all
    select 5 as x
) a
