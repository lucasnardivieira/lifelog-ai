-- Validated questionnaires, scored. Never diagnostic: flags only suggest talking to someone.
with scored as (
    select
        event_id,
        event_date as day,
        instrument,
        responses,
        case instrument
            -- WHO-5: raw 0–25 ×4 → 0–100
            when 'who5' then list_sum(responses) * 4
            -- PSS-10: items 4, 5, 7, 8 are positively worded → reverse (4 − x); total 0–40
            when 'pss10' then list_sum(
                [case when i in (4, 5, 7, 8) then 4 - responses[i] else responses[i] end
                 for i in range(1, 11)]
            )
            when 'life_satisfaction' then responses[1]
        end as score,
        case instrument when 'who5' then 100 when 'pss10' then 40 else 10 end as max_score
    from {{ ref('stg_events') }}
    where event_type = 'assessment'
)

select
    *,
    -- WHO-5 raw < 13 (score < 52) is the common "low well-being" flag (Topp et al., 2015)
    instrument = 'who5' and score < 52 as low_wellbeing_flag
from scored
order by day, instrument
