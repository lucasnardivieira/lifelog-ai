/** Mirrors the JSON written by src/lifelog/export.py. */
export type AreaKey = 'body' | 'mind' | 'growth' | 'money_social'
export type Quadrant = 'yellow' | 'red' | 'blue' | 'green'

export interface Day {
  day: string
  week_start: string
  iso_weekday: number
  is_weekend: boolean
  event_count?: number
  sleep_hours?: number
  sleep_quality?: number
  sleep_rested?: number
  bedtime?: string
  wake_time?: string
  bedtime_min?: number
  wake_min?: number
  sleep_onset_minutes?: number
  awakenings?: number
  waso_minutes?: number
  time_in_bed_minutes?: number
  sleep_efficiency?: number
  sleep_midpoint_min?: number
  sleep_midpoint_sd_7d?: number
  energy?: number
  exercise_minutes?: number
  exercise_kinds?: string
  healthy_meals?: number
  junk_meals?: number
  valence?: number
  arousal?: number
  mood?: number
  quadrant?: Quadrant
  affect_checkins?: number
  stress?: number
  autonomy?: number
  competence?: number
  relatedness?: number
  gratitude_count?: number
  journal_count?: number
  activity_pleasure?: number
  activity_mastery?: number
  study_minutes?: number
  study_topics?: string
  reading_pages?: number
  work_minutes?: number
  is_deadline?: boolean
  habits_tracked?: number
  habits_done?: number
  spend_total?: number
  spend_discretionary?: number
  income_total?: number
  social_count?: number
  social_with?: string
  body_score: number
  mind_score: number
  growth_score: number
  money_social_score: number
}

export interface Week {
  week_start: string
  days: number
  avg_sleep_hours?: number
  avg_sleep_efficiency?: number
  sleep_midpoint_sd?: number
  social_jetlag_minutes?: number
  avg_valence?: number
  avg_arousal?: number
  avg_mood?: number
  avg_stress?: number
  avg_energy?: number
  avg_autonomy?: number
  avg_competence?: number
  avg_relatedness?: number
  avg_activity_pleasure?: number
  exercise_minutes: number
  exercise_days: number
  study_minutes: number
  study_days: number
  reading_pages: number
  work_minutes: number
  habit_completion?: number
  spend_total: number
  spend_discretionary: number
  social_count: number
  has_deadline: boolean
  days_yellow: number
  days_red: number
  days_blue: number
  days_green: number
  distinct_emotions?: number
  distinct_negative_emotions?: number
  who5_score?: number
  body_score: number
  mind_score: number
  growth_score: number
  money_social_score: number
}

export interface AffectPoint {
  ts: string
  day: string
  valence: number
  arousal: number
  quadrant: Quadrant
  emotions?: string[]
  text?: string
}

export interface EmotionWeek {
  week_start: string
  word: string
  quadrant: Quadrant
  is_negative: boolean
  mentions: number
}

export interface Assessment {
  day: string
  instrument: 'who5' | 'pss10' | 'life_satisfaction'
  score: number
  max_score: number
  low_wellbeing_flag: boolean
}

export interface Habit {
  habit: string
  if_then: string
  started: string
  days: number
  completion: number
  points: { day: string; done: boolean; strength: number }[]
}

export interface Insight {
  id: string
  kind: 'compare' | 'correlation'
  text: string
  strength: number
  positive: boolean | null
  x: string
  y: string
  construct: string
  details: {
    yes?: { label: string; mean_deviation: number; days: number }
    no?: { label: string; mean_deviation: number; days: number }
    difference?: number
    ci95?: [number, number]
    effect_size?: number
    lag_days?: number
    unit?: string
    outcome_label?: string
    r?: number
    n?: number
    points?: [number, number][]
  }
}

export interface LogEvent {
  id: string
  ts: string
  day: string
  type: string
  area: AreaKey
  score?: number
  hours?: number
  minutes?: number
  pages?: number
  amount?: number
  category?: string
  label?: string
  note?: string
  text?: string
}

export interface Instrument {
  name: string
  max: number
  higher_is_better: boolean
  reference?: number
  reference_label?: string
  source: string
}

export interface Payload {
  generated_at: string
  sample: boolean
  range: { start: string; end: string }
  areas: Record<AreaKey, { label: string; emoji: string }>
  goals: Record<string, number>
  quadrants: Record<Quadrant, { label: string; hint: string }>
  vocabulary: { word: string; valence: number; arousal: number; quadrant: Quadrant }[]
  instruments: Record<Assessment['instrument'], Instrument>
  support: {
    title: string
    text: string
    highlight: boolean
    contacts: { name: string; detail: string; href: string }[]
  }
  days: Day[]
  weeks: Week[]
  spending: { day: string; category: string; transactions: number; amount: number }[]
  study: { day: string; topic: string; sessions: number; minutes: number }[]
  affect: AffectPoint[]
  emotions: EmotionWeek[]
  assessments: Assessment[]
  habits: Habit[]
  events: LogEvent[]
  insights: Insight[]
}
