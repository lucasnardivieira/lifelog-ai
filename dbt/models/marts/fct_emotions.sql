-- Emotion vocabulary usage per week (granularity).
select
    cast(date_trunc('week', event_date) as date) as week_start,
    word,
    quadrant,
    is_negative,
    count(*) as mentions
from {{ ref('int_emotion_mentions') }}
group by all
order by week_start, mentions desc
