with date_spine as (
    select date('2023-01-01') as date_day
    union all
    select date('2023-01-02')
    union all
    select date('2023-01-03')
    union all
    select date('2023-01-04')
    union all
    select date('2023-01-05')
)
select
    date_day,
    extract(dayofweek from date_day) as day_of_week,
    extract(week from date_day) as week_of_year
from date_spine
