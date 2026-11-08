import type { AreaKey } from '../types'

export const AREA_ORDER: AreaKey[] = ['body', 'mind', 'growth', 'money_social']
export const SCORE_KEY = {
  body: 'body_score',
  mind: 'mind_score',
  growth: 'growth_score',
  money_social: 'money_social_score',
} as const
export const AREA_IMG = {
  body: 'area-body',
  mind: 'area-mind',
  growth: 'area-growth',
  money_social: 'area-money-social',
} as const
