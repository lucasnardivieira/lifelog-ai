import { describe, expect, it } from 'vitest'
import type { Day, Payload } from '../types'
import { periodStart, previousWindow } from './period'

const payload = { range: { start: '2026-05-10', end: '2026-11-08' } } as Payload
const days = Array.from({ length: 60 }, (_, i) => {
  const d = new Date('2026-09-10T12:00:00')
  d.setDate(d.getDate() + i)
  return { day: d.toISOString().slice(0, 10) } as Day
})

describe('period', () => {
  it('starts N-1 days before the last day', () => {
    expect(periodStart(payload, '30')).toBe('2026-10-10')
  })

  it('never starts before the data', () => {
    expect(periodStart(payload, 'all')).toBe('2026-05-10')
    expect(periodStart({ range: { start: '2026-11-01', end: '2026-11-08' } } as Payload, '90')).toBe('2026-11-01')
  })

  it('returns the same-length window before the period', () => {
    const prev = previousWindow(days, days[40].day)
    expect(prev).toHaveLength(20)
    expect(prev[prev.length - 1].day).toBe(days[39].day)
  })
})
