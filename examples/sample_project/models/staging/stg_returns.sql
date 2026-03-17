select
    return_id,
    order_id,
    order_item_id,
    return_date::date as return_date,
    reason,
    status,
    refund_amount
from {{ source('main', 'raw_returns') }}
