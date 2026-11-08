select event_id from {{ ref('fct_assessments') }}
where score < 0 or score > max_score
