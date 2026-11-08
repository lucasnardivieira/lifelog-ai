-- One row per calendar day (gap-free), with metrics and 0–100 life scores per area.
with bounds as (
    select min(event_date) as first_day, max(event_date) as last_day
    from {{ ref('stg_events') }}
),

spine as (
    select cast(d as date) as day
    from bounds, generate_series(first_day, last_day, interval 1 day) as t(d)
),

daily as (
    select
        s.day,
        cast(date_trunc('week', s.day) as date) as week_start,
        isodow(s.day) as iso_weekday,
        isodow(s.day) >= 6 as is_weekend,
        m.*  exclude (event_date)
    from spine as s
    left join {{ ref('int_daily_metrics') }} as m on m.event_date = s.day
)

select
    *,
    -- Heuristic scores: each component is scaled to 0–1, then averaged (nulls ignored).
    round(100 * (
        coalesce(least(sleep_hours / {{ var('sleep_goal_hours') }}, 1), 0)
        + coalesce(sleep_quality / 5, 0)
        + coalesce(energy / 5, 0)
        + case when exercise_minutes > 0 then 1 else 0.4 end
    ) / 4) as body_score,
    round(100 * (
        coalesce(mood / 5, 0.6)
        + coalesce((6 - stress) / 5, 0.6)
        + case when gratitude_count > 0 or journal_count > 0 then 1 else 0.6 end
    ) / 3) as mind_score,
    round(100 * (
        least(coalesce(study_minutes, 0) / {{ var('study_goal_minutes') }}, 1)
        + least(coalesce(reading_pages, 0) / {{ var('reading_goal_pages') }}, 1)
    ) / 2) as growth_score,
    round(100 * (
        case when social_count > 0 then 1 else 0.5 end
        + case
            when coalesce(spend_discretionary, 0) <= {{ var('discretionary_budget_brl') }} then 1
            else {{ var('discretionary_budget_brl') }} / spend_discretionary
        end
    ) / 2) as money_social_score
from daily
order by day
