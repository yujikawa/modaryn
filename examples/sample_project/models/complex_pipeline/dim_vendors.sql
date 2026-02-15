select
    (row_number() over (order by 1)) as vendor_id,
    'Vendor ' || (row_number() over (order by 1)) as vendor_name
from (
    select 1 as x union all
    select 2 as x union all
    select 3 as x
) a
