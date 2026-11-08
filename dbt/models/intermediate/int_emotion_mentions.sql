-- One row per emotion word mentioned in an affect check-in.
select
    e.event_id,
    e.event_date,
    e.occurred_at_local,
    m.word,
    v.quadrant,
    v.valence < 0 as is_negative
from {{ ref('stg_events') }} as e,
    unnest(e.emotions) as m(word)
left join {{ ref('emotion_vocabulary') }} as v on v.word = m.word
where e.event_type = 'affect'
