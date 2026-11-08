-- Monday-based weeks: the numbers behind the Sunday report.
with emotions as (
    select
        week_start,
        count(distinct word) as distinct_emotions,
        count(distinct word) filter (where is_negative) as distinct_negative_emotions
    from {{ ref('fct_emotions') }}
    group by week_start
),

who5 as (
    select cast(date_trunc('week', day) as date) as week_start, max(score) as who5_score
    from {{ ref('fct_assessments') }}
    where instrument = 'who5'
    group by 1
),

days as (
    select
        week_start,
        count(*) as days,
        round(avg(sleep_hours), 2) as avg_sleep_hours,
        round(avg(sleep_efficiency), 1) as avg_sleep_efficiency,
        round(stddev_samp(sleep_midpoint_min)) as sleep_midpoint_sd,
        round(avg(sleep_midpoint_min) filter (where is_weekend)
            - avg(sleep_midpoint_min) filter (where not is_weekend)) as social_jetlag_minutes,
        round(avg(valence), 2) as avg_valence,
        round(avg(arousal), 2) as avg_arousal,
        round(avg(mood), 2) as avg_mood,
        round(avg(stress), 2) as avg_stress,
        round(avg(energy), 2) as avg_energy,
        round(avg(autonomy), 2) as avg_autonomy,
        round(avg(competence), 2) as avg_competence,
        round(avg(relatedness), 2) as avg_relatedness,
        round(avg(activity_pleasure), 1) as avg_activity_pleasure,
        sum(exercise_minutes) as exercise_minutes,
        count(*) filter (where exercise_minutes > 0) as exercise_days,
        sum(study_minutes) as study_minutes,
        count(*) filter (where study_minutes > 0) as study_days,
        sum(reading_pages) as reading_pages,
        sum(work_minutes) as work_minutes,
        round(sum(habits_done) / nullif(sum(habits_tracked), 0), 2) as habit_completion,
        round(sum(spend_total), 2) as spend_total,
        round(sum(spend_discretionary), 2) as spend_discretionary,
        sum(social_count) as social_count,
        bool_or(is_deadline) as has_deadline,
        count(*) filter (where quadrant = 'yellow') as days_yellow,
        count(*) filter (where quadrant = 'red') as days_red,
        count(*) filter (where quadrant = 'blue') as days_blue,
        count(*) filter (where quadrant = 'green') as days_green,
        round(avg(body_score)) as body_score,
        round(avg(mind_score)) as mind_score,
        round(avg(growth_score)) as growth_score,
        round(avg(money_social_score)) as money_social_score
    from {{ ref('fct_daily') }}
    group by week_start
)

select d.*, e.distinct_emotions, e.distinct_negative_emotions, w.who5_score
from days as d
left join emotions as e using (week_start)
left join who5 as w using (week_start)
order by week_start
