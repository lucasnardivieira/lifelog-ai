import { useLife } from '../lib/context'
import { hoursDec, longDate, money, timeOf } from '../lib/format'
import { QUADRANT_EMOJI, QUADRANT_SHORT, QUADRANT_TOKEN } from '../lib/theme'
import type { LogEvent } from '../types'
import { Card } from './ui'

export const EVENT_ICON: Record<string, string> = {
  sleep: '😴',
  exercise: '🏃',
  energy: '⚡',
  meal: '🍽️',
  affect: '◐',
  mood: '🙂',
  stress: '🌡️',
  needs: '△',
  assessment: '📋',
  gratitude: '🙏',
  journal: '✎',
  study: '📚',
  reading: '📖',
  work: '💼',
  habit: '↗',
  expense: '💸',
  income: '💰',
  social: '👥',
}

export function EventLine({ e }: { e: LogEvent }) {
  return (
    <li className="flex gap-3 py-1.5">
      <span className="tnum w-11 shrink-0 text-xs text-muted">{timeOf(e.ts)}</span>
      <span aria-hidden className="w-5 shrink-0 text-center">{EVENT_ICON[e.type] ?? '•'}</span>
      <span className={`text-sm ${e.type === 'journal' || e.type === 'gratitude' ? 'italic text-ink' : 'text-ink-2'}`}>
        {e.text ?? e.type}
      </span>
    </li>
  )
}

export function DayDetail({ day, onClose }: { day: string; onClose?: () => void }) {
  const { payload, t } = useLife()
  const row = payload.days.find((d) => d.day === day)
  const events = payload.events.filter((e) => e.day === day)
  return (
    <Card
      title={longDate(day)}
      subtitle={`${events.length} registros`}
      action={
        onClose && (
          <button onClick={onClose} className="text-muted hover:text-ink" aria-label="Fechar">
            ✕
          </button>
        )
      }
    >
      {row && (
        <div className="mb-3 flex flex-wrap gap-2 text-xs">
          {row.quadrant && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-3 py-1">
              <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[row.quadrant]] }} />
              {QUADRANT_EMOJI[row.quadrant]} {QUADRANT_SHORT[row.quadrant]}
            </span>
          )}
          {row.sleep_hours != null && (
            <span className="rounded-full bg-surface-2 px-3 py-1">
              😴 {hoursDec(row.sleep_hours)} · eficiência {row.sleep_efficiency}%
            </span>
          )}
          {row.is_deadline && <span className="rounded-full bg-surface-2 px-3 py-1">⏳ dia de prazo</span>}
          {row.spend_discretionary ? (
            <span className="rounded-full bg-surface-2 px-3 py-1">💸 {money(row.spend_discretionary)} variável</span>
          ) : null}
        </div>
      )}
      <ul className="max-h-[420px] divide-y divide-[color:var(--grid)] overflow-y-auto">
        {events.map((e) => (
          <EventLine key={e.id} e={e} />
        ))}
      </ul>
    </Card>
  )
}
