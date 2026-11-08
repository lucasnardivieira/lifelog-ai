-- Pivot events into one row per day that has any event.
select
    event_date,

    -- body: Consensus Sleep Diary
    max(hours) filter (where event_type = 'sleep') as sleep_hours,
    max(score) filter (where event_type = 'sleep') as sleep_quality,
    max(rested) filter (where event_type = 'sleep') as sleep_rested,
    max(bedtime) filter (where event_type = 'sleep') as bedtime,
    max(wake_time) filter (where event_type = 'sleep') as wake_time,
    max(bedtime_min_after_noon) filter (where event_type = 'sleep') as bedtime_min,
    max(wake_min_after_noon) filter (where event_type = 'sleep') as wake_min,
    max(sol_minutes) filter (where event_type = 'sleep') as sleep_onset_minutes,
    max(awakenings) filter (where event_type = 'sleep') as awakenings,
    max(waso_minutes) filter (where event_type = 'sleep') as waso_minutes,
    avg(score) filter (where event_type = 'energy') as energy,
    coalesce(sum(minutes) filter (where event_type = 'exercise'), 0) as exercise_minutes,
    string_agg(distinct category, ', ') filter (where event_type = 'exercise') as exercise_kinds,
    count(*) filter (where event_type = 'meal' and category = 'saudável') as healthy_meals,
    count(*) filter (where event_type = 'meal' and category = 'besteira') as junk_meals,

    -- mind: core affect (−2…+2), SDT needs (1–5), stress
    avg(valence) filter (where valence is not null) as valence,
    avg(arousal) filter (where arousal is not null) as arousal,
    count(*) filter (where event_type = 'affect') as affect_checkins,
    avg(score) filter (where event_type = 'stress') as stress,
    max(autonomy) filter (where event_type = 'needs') as autonomy,
    max(competence) filter (where event_type = 'needs') as competence,
    max(relatedness) filter (where event_type = 'needs') as relatedness,
    count(*) filter (where event_type = 'gratitude') as gratitude_count,
    count(*) filter (where event_type = 'journal') as journal_count,

    -- behavioral activation: ratings on activities (0–10)
    avg(pleasure) filter (where pleasure is not null) as activity_pleasure,
    avg(mastery) filter (where mastery is not null) as activity_mastery,

    -- growth
    coalesce(sum(minutes) filter (where event_type = 'study'), 0) as study_minutes,
    string_agg(distinct category, ', ') filter (where event_type = 'study') as study_topics,
    coalesce(sum(pages) filter (where event_type = 'reading'), 0) as reading_pages,
    coalesce(sum(minutes) filter (where event_type = 'work'), 0) as work_minutes,
    coalesce(bool_or(event_type = 'work' and category = 'prazo'), false) as is_deadline,
    count(*) filter (where event_type = 'habit') as habits_tracked,
    count(*) filter (where event_type = 'habit' and done) as habits_done,

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
