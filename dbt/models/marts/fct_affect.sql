-- Every affect check-in (for the affect grid and quadrant strip).
select
    event_id,
    occurred_at_local,
    event_date as day,
    valence,
    arousal,
    case
        when valence >= 0 and arousal > 0 then 'yellow'
        when valence >= 0 then 'green'
        when arousal > 0 then 'red'
        else 'blue'
    end as quadrant,
    emotions,
    raw_text
from {{ ref('stg_events') }}
where event_type = 'affect'
order by occurred_at_local
