select
    customer_id,
    customer_name,
    customer_segment
from {{ source('sample_project', 'customers') }}