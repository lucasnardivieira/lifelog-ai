import { describe, expect, it } from 'vitest'
import { clockFromNoon, hoursMin, mean, signed } from './format'

describe('format', () => {
  it('converts minutes after noon to clock time across midnight', () => {
    expect(clockFromNoon(690)).toBe('23:30')
    expect(clockFromNoon(1140)).toBe('07:00')
  })

  it('formats durations', () => {
    expect(hoursMin(65)).toBe('1h05')
    expect(hoursMin(40)).toBe('40min')
    expect(hoursMin(null)).toBe('—')
  })

  it('signs numbers in pt-BR', () => {
    expect(signed(0.84)).toBe('+0,8')
    expect(signed(-1.25, 2)).toBe('−1,25')
    expect(signed(0)).toBe('±0,0')
  })

  it('ignores missing values in the mean', () => {
    expect(mean([1, null, 3, undefined])).toBe(2)
    expect(mean([])).toBeNull()
  })
})
