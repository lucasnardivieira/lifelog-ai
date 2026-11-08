select
    event_date as day,
    category,
    count(*) as transactions,
    round(sum(amount), 2) as amount
from {{ ref('stg_events') }}
where event_type = 'expense'
group by event_date, category
order by day, category
