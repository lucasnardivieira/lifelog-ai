-- The diary: every event with the original message.
select
    event_id,
    occurred_at_local,
    event_date as day,
    event_type,
    area,
    score,
    hours,
    minutes,
    pages,
    amount,
    category,
    label,
    note,
    raw_text
from {{ ref('stg_events') }}
order by occurred_at_local, event_id
