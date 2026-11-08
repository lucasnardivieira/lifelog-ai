-- Pivot events into one row per day that has any event.
select
    event_date,

    -- body
    max(hours) filter (where event_type = 'sleep') as sleep_hours,
    max(score) filter (where event_type = 'sleep') as sleep_quality,
    avg(score) filter (where event_type = 'energy') as energy,
    coalesce(sum(minutes) filter (where event_type = 'exercise'), 0) as exercise_minutes,
    string_agg(distinct category, ', ') filter (where event_type = 'exercise') as exercise_kinds,
    count(*) filter (where event_type = 'meal' and category = 'saudável') as healthy_meals,
    count(*) filter (where event_type = 'meal' and category = 'besteira') as junk_meals,

    -- mind
    avg(score) filter (where event_type = 'mood') as mood,
    avg(score) filter (where event_type = 'stress') as stress,
    count(*) filter (where event_type = 'gratitude') as gratitude_count,
    count(*) filter (where event_type = 'journal') as journal_count,

    -- growth
    coalesce(sum(minutes) filter (where event_type = 'study'), 0) as study_minutes,
    string_agg(distinct category, ', ') filter (where event_type = 'study') as study_topics,
    coalesce(sum(pages) filter (where event_type = 'reading'), 0) as reading_pages,
    coalesce(sum(minutes) filter (where event_type = 'work'), 0) as work_minutes,
    bool_or(event_type = 'work' and category = 'prazo') as is_deadline,

    -- money & social
    coalesce(sum(amount) filter (where event_type = 'expense'), 0) as spend_total,
    coalesce(sum(amount) filter (
        where event_type = 'expense' and category not in ('moradia', 'contas', 'assinaturas')
    ), 0) as spend_discretionary,
    coalesce(sum(amount) filter (where event_type = 'income'), 0) as income_total,
    count(*) filter (where event_type = 'social') as social_count,
    string_agg(distinct category, ', ') filter (where event_type = 'social') as social_with,

    count(*) as event_count
from {{ ref('stg_events') }}
group by event_date
