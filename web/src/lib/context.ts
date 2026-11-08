import { createContext, useContext } from 'react'
import type { Day, Payload } from '../types'
import type { Period } from './period'
import type { Tokens } from './theme'

export interface Life {
  payload: Payload
  period: Period
  start: string
  days: Day[] // days inside the selected period
  prevDays: Day[] // same-length window before it
  t: Tokens
  openSupport: () => void
  go: (page: PageKey) => void
}

export type PageKey =
  | 'overview' | 'tracks' | 'calendar' | 'emotions' | 'wellbeing'
  | 'habits' | 'areas' | 'patterns' | 'diary' | 'week'

export const LifeContext = createContext<Life | null>(null)

export function useLife(): Life {
  const ctx = useContext(LifeContext)
  if (!ctx) throw new Error('useLife outside provider')
  return ctx
}
