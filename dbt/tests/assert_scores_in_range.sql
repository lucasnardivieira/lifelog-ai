select day
from {{ ref('fct_daily') }}
where body_score not between 0 and 100
   or mind_score not between 0 and 100
   or growth_score not between 0 and 100
   or money_social_score not between 0 and 100
