with date_spine as (
    select unnest(generate_series(
        '2023-01-01'::date,
        '2023-12-31'::date,
        interval '1 day'
    ))::date as date_day
)
select
    date_day,
    extract(year from date_day)::int as year,
    extract(month from date_day)::int as month,
    extract(day from date_day)::int as day,
    extract(quarter from date_day)::int as quarter,
    extract(week from date_day)::int as week_of_year,
    extract(dow from date_day)::int as day_of_week,
    to_char(date_day, 'Month') as month_name,
    to_char(date_day, 'Day') as day_name,
    date_trunc('month', date_day)::date as month_start,
    date_trunc('quarter', date_day)::date as quarter_start,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from date_spine
