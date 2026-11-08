-- Monday-based weeks: the numbers behind the Sunday report.
select
    week_start,
    count(*) as days,
    round(avg(sleep_hours), 2) as avg_sleep_hours,
    round(avg(mood), 2) as avg_mood,
    round(avg(stress), 2) as avg_stress,
    round(avg(energy), 2) as avg_energy,
    sum(exercise_minutes) as exercise_minutes,
    count(*) filter (where exercise_minutes > 0) as exercise_days,
    sum(study_minutes) as study_minutes,
    count(*) filter (where study_minutes > 0) as study_days,
    sum(reading_pages) as reading_pages,
    sum(work_minutes) as work_minutes,
    round(sum(spend_total), 2) as spend_total,
    round(sum(spend_discretionary), 2) as spend_discretionary,
    sum(social_count) as social_count,
    bool_or(is_deadline) as has_deadline,
    round(avg(body_score)) as body_score,
    round(avg(mind_score)) as mind_score,
    round(avg(growth_score)) as growth_score,
    round(avg(money_social_score)) as money_social_score
from {{ ref('fct_daily') }}
group by week_start
order by week_start
