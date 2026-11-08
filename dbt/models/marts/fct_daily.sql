-- One row per calendar day (gap-free): metrics, derived sleep measures and 0–100 area scores.
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
        m.* exclude (event_date)
    from spine as s
    left join {{ ref('int_daily_metrics') }} as m on m.event_date = s.day
),

sleep as (
    select
        *,
        -- time in bed and efficiency (Carney et al., 2012)
        (wake_min - bedtime_min + 1440) % 1440 as time_in_bed_minutes,
        round(100.0 * sleep_hours * 60 / nullif((wake_min - bedtime_min + 1440) % 1440, 0), 1)
            as sleep_efficiency,
        -- sleep midpoint in minutes after noon (regularity / social jetlag)
        bedtime_min + ((wake_min - bedtime_min + 1440) % 1440) / 2 as sleep_midpoint_min
    from daily
)

select
    *,
    -- regularity: spread of the sleep midpoint over the trailing 7 nights (lower = steadier)
    round(stddev_samp(sleep_midpoint_min) over (
        order by day rows between 6 preceding and current row
    )) as sleep_midpoint_sd_7d,
    -- mood on the familiar 1–5 scale, derived from valence
    round(valence + 3, 2) as mood,
    case
        when valence is null then null
        when valence >= 0 and arousal > 0 then 'yellow'
        when valence >= 0 then 'green'
        when arousal > 0 then 'red'
        else 'blue'
    end as quadrant,

    -- Heuristic area scores: each component is scaled to 0–1 and averaged.
    round(100 * (
        coalesce(least(sleep_hours / {{ var('sleep_goal_hours') }}, 1), 0)
        + coalesce(sleep_quality / 5, 0)
        + coalesce(least(sleep_efficiency / 85, 1), 0)
        + coalesce(energy / 5, 0)
        + case when exercise_minutes > 0 then 1 else 0.4 end
    ) / 5) as body_score,
    round(100 * (
        coalesce((valence + 2) / 4, 0.5)
        + coalesce((6 - stress) / 5, 0.6)
        + coalesce((autonomy + competence + relatedness) / 15, 0.6)
        + case when gratitude_count > 0 or journal_count > 0 then 1 else 0.6 end
    ) / 4) as mind_score,
    round(100 * (
        least(coalesce(study_minutes, 0) / {{ var('study_goal_minutes') }}, 1)
        + least(coalesce(reading_pages, 0) / {{ var('reading_goal_pages') }}, 1)
        + coalesce(habits_done / nullif(habits_tracked, 0), 0.5)
    ) / 3) as growth_score,
    round(100 * (
        case when social_count > 0 then 1 else 0.5 end
        + case
            when coalesce(spend_discretionary, 0) <= {{ var('discretionary_budget_brl') }} then 1
            else {{ var('discretionary_budget_brl') }} / spend_discretionary
        end
    ) / 2) as money_social_score
from sleep
order by day
