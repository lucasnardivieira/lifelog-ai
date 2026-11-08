import type { Day, Payload } from '../types'
import { parseDay } from './format'

export type Period = '30' | '90' | '183' | 'all'

export const PERIODS: { key: Period; label: string }[] = [
  { key: '30', label: '30 dias' },
  { key: '90', label: '90 dias' },
  { key: '183', label: '6 meses' },
  { key: 'all', label: 'Tudo' },
]

export function periodStart(payload: Payload, period: Period): string {
  if (period === 'all') return payload.range.start
  const end = parseDay(payload.range.end)
  end.setDate(end.getDate() - Number(period) + 1)
  const iso = end.toISOString().slice(0, 10)
  return iso < payload.range.start ? payload.range.start : iso
}

export const inRange = <T extends { day: string }>(rows: T[], start: string) =>
  rows.filter((r) => r.day >= start)

/** the same-length window right before `start`, for "vs previous period" deltas */
export function previousWindow(days: Day[], start: string): Day[] {
  const idx = days.findIndex((d) => d.day >= start)
  if (idx <= 0) return []
  const len = days.length - idx
  return days.slice(Math.max(0, idx - len), idx)
}
