with campaign_data as (
    select
        'campaign_a' as campaign_id,
        '2023-01-01'::date as campaign_start_date,
        '2023-01-31'::date as campaign_end_date,
        1000.00 as total_spend,
        50 as total_conversions
    union all
    select
        'campaign_b' as campaign_id,
        '2023-02-01'::date as campaign_start_date,
        '2023-02-28'::date as campaign_end_date,
        1500.00 as total_spend,
        75 as total_conversions
)
select * from campaign_data
