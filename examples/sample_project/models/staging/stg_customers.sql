select
    customer_id,
    customer_name,
    email,
    signup_date::date as signup_date,
    country,
    city,
    segment,
    age_group,
    referral_source
from {{ source('main', 'raw_customers') }}
