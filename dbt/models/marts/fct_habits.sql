select
    event_date as day,
    habit,
    any_value(if_then) as if_then,
    bool_or(done) as done
from {{ ref('stg_events') }}
where event_type = 'habit'
group by event_date, habit
order by habit, day
