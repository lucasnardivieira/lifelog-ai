const nf1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 1 })
const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 })
const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })

export const fmt1 = (n: number | null | undefined) => (n == null || Number.isNaN(n) ? '—' : nf1.format(n))
export const fmt0 = (n: number | null | undefined) => (n == null || Number.isNaN(n) ? '—' : nf0.format(n))
export const money = (n: number | null | undefined) => (n == null ? '—' : brl.format(n))

export const hoursMin = (minutes: number | null | undefined) => {
  if (minutes == null) return '—'
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return h ? `${h}h${m ? String(m).padStart(2, '0') : ''}` : `${m}min`
}

export const hoursDec = (hours: number | null | undefined) => (hours == null ? '—' : hoursMin(hours * 60))

/** minutes after noon → "HH:MM" clock time */
export const clockFromNoon = (minutes: number) => {
  const total = Math.round(720 + minutes) % 1440
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const WEEKDAYS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']

export const parseDay = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`)
export const shortDate = (iso: string) => {
  const d = parseDay(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`
}
export const longDate = (iso: string) => {
  const d = parseDay(iso)
  return `${WEEKDAYS[d.getDay()]}, ${d.getDate()} de ${MONTHS[d.getMonth()]}`
}
export const weekday = (iso: string) => WEEKDAYS[parseDay(iso).getDay()]
export const timeOf = (ts: string) => ts.slice(11, 16)

export const mean = (xs: (number | null | undefined)[]) => {
  const v = xs.filter((x): x is number => x != null && !Number.isNaN(x))
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
}
export const sum = (xs: (number | null | undefined)[]) =>
  xs.reduce<number>((a, b) => a + (b ?? 0), 0)

export const signed = (n: number | null, digits = 1) =>
  n == null ? '—' : `${n > 0 ? '+' : n < 0 ? '−' : '±'}${Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits })}`
