select
    (row_number() over (order by 1)) as channel_id,
    case (row_number() over (order by 1))
        when 1 then 'Organic Search'
        when 2 then 'Paid Search'
        when 3 then 'Social Media'
        when 4 then 'Email'
        else 'Other'
    end as channel_name
from (
    select 1 as x union all select 2 union all select 3 union all select 4 union all select 5
) a
