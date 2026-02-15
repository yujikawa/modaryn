select
    (row_number() over (order by 1)) as visit_id,
    'page_' || (row_number() over (order by 1)) as page_id,
    '2023-01-01'::date as visit_date,
    (row_number() over (order by 1)) * 5 as page_views
from (
    select 1 as x union all select 2 union all select 3 union all select 4 union all select 5
    union all select 6 union all select 7 union all select 8 union all select 9 union all select 10
) a
