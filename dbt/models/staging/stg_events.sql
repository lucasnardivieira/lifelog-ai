-- One row per event, typed, with local date/time and life area.
-- occurred_at is ISO-8601 with the local offset (e.g. 2026-11-08T21:30:00-03:00),
-- so the first 19 chars are already local wall-clock time.
-- Raw layer: append-only JSON Lines (synthetic generator or Telegram bot).
-- Columns are declared explicitly so optional fields exist even if no event uses them yet.
with source as (
    select *
    from read_json(
        '{{ env_var("LIFELOG_EVENTS", "data/synthetic/events.jsonl") }}',
        format = 'newline_delimited',
        columns = {
            'event_id': 'VARCHAR', 'occurred_at': 'VARCHAR', 'type': 'VARCHAR',
            'source': 'VARCHAR', 'score': 'INTEGER', 'hours': 'DOUBLE', 'minutes': 'INTEGER',
            'pages': 'INTEGER', 'amount': 'DOUBLE', 'currency': 'VARCHAR',
            'category': 'VARCHAR', 'label': 'VARCHAR', 'note': 'VARCHAR', 'raw_text': 'VARCHAR',
            'bedtime': 'VARCHAR', 'wake_time': 'VARCHAR', 'sol_minutes': 'INTEGER',
            'awakenings': 'INTEGER', 'waso_minutes': 'INTEGER', 'rested': 'INTEGER',
            'valence': 'INTEGER', 'arousal': 'INTEGER', 'emotions': 'VARCHAR[]',
            'autonomy': 'INTEGER', 'competence': 'INTEGER', 'relatedness': 'INTEGER',
            'pleasure': 'INTEGER', 'mastery': 'INTEGER',
            'instrument': 'VARCHAR', 'responses': 'INTEGER[]',
            'habit': 'VARCHAR', 'done': 'BOOLEAN', 'if_then': 'VARCHAR'
        }
    )
)

select
    event_id,
    cast(left(occurred_at, 19) as timestamp) as occurred_at_local,
    cast(left(occurred_at, 10) as date) as event_date,
    type as event_type,
    case
        when type in ('sleep', 'exercise', 'energy', 'meal') then 'body'
        when type in ('affect', 'mood', 'stress', 'needs', 'assessment', 'gratitude', 'journal')
            then 'mind'
        when type in ('study', 'reading', 'work', 'habit') then 'growth'
        when type in ('expense', 'income', 'social') then 'money_social'
    end as area,
    source,
    score,
    hours,
    minutes,
    pages,
    amount,
    coalesce(currency, case when amount is not null then 'BRL' end) as currency,
    category,
    label,
    note,
    raw_text,
    -- sleep diary: clock times → minutes after noon, so a night never wraps past midnight
    bedtime,
    wake_time,
    (cast(split_part(bedtime, ':', 1) as integer) * 60 + cast(split_part(bedtime, ':', 2) as integer)
        + 720) % 1440 as bedtime_min_after_noon,
    (cast(split_part(wake_time, ':', 1) as integer) * 60
        + cast(split_part(wake_time, ':', 2) as integer) + 720) % 1440 as wake_min_after_noon,
    sol_minutes,
    awakenings,
    waso_minutes,
    rested,
    -- core affect: legacy 1–5 mood is mapped onto valence
    coalesce(valence, case when type = 'mood' then score - 3 end) as valence,
    arousal,
    emotions,
    autonomy,
    competence,
    relatedness,
    pleasure,
    mastery,
    instrument,
    responses,
    habit,
    done,
    if_then
from source
