select
    event_date as day,
    category as topic,
    count(*) as sessions,
    sum(minutes) as minutes
from {{ ref('stg_events') }}
where event_type = 'study'
group by event_date, category
order by day, topic
