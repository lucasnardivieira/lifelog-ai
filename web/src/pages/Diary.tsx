import { useMemo, useState } from 'react'
import { EventLine } from '../components/DayDetail'
import { Card, Chip, Illustration } from '../components/ui'
import { useLife } from '../lib/context'
import { longDate } from '../lib/format'
import { QUADRANT_EMOJI, QUADRANT_SHORT, QUADRANT_TOKEN } from '../lib/theme'

const FILTERS: { key: string; label: string; types: string[] | null }[] = [
  { key: 'all', label: 'Tudo', types: null },
  { key: 'reflection', label: '✎ Diário e gratidão', types: ['journal', 'gratitude'] },
  { key: 'affect', label: '◐ Emoções', types: ['affect', 'stress', 'needs'] },
  { key: 'sleep', label: '😴 Sono e corpo', types: ['sleep', 'exercise', 'energy', 'meal'] },
  { key: 'growth', label: '📚 Estudo e trabalho', types: ['study', 'reading', 'work', 'habit'] },
  { key: 'money', label: '💸 Dinheiro e social', types: ['expense', 'income', 'social'] },
]
const PAGE = 10

export function Diary() {
  const { payload, start, t } = useLife()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [limit, setLimit] = useState(PAGE)
  const types = FILTERS.find((f) => f.key === filter)!.types

  const byDay = useMemo(() => {
    const q = query.trim().toLowerCase()
    const events = payload.events.filter(
      (e) => e.day >= start && (!types || types.includes(e.type)) && (!q || (e.text ?? '').toLowerCase().includes(q)),
    )
    const groups = new Map<string, typeof events>()
    events.forEach((e) => groups.set(e.day, [...(groups.get(e.day) ?? []), e]))
    return [...groups.entries()].sort((a, b) => (a[0] < b[0] ? 1 : -1))
  }, [payload.events, query, start, types])

  const dayRow = new Map(payload.days.map((d) => [d.day, d]))

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setLimit(PAGE)
          }}
          placeholder="Buscar no diário… (ex.: cansado, dbt, namorado)"
          aria-label="Buscar no diário"
          className="w-full rounded-full border border-line bg-surface px-4 py-2 text-sm outline-none focus:border-[color:var(--axis)] sm:w-80"
        />
        {FILTERS.map((f) => (
          <Chip
            key={f.key}
            active={filter === f.key}
            onClick={() => {
              setFilter(f.key)
              setLimit(PAGE)
            }}
          >
            {f.label}
          </Chip>
        ))}
      </div>

      {byDay.length === 0 && (
        <Card>
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <Illustration name="empty-state" alt="" tile className="h-24 w-24" />
            <p className="text-sm text-ink-2">Nada encontrado com esses filtros.</p>
          </div>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {byDay.slice(0, limit).map(([day, events]) => {
          const row = dayRow.get(day)
          return (
            <Card
              key={day}
              title={longDate(day)}
              subtitle={`${events.length} registro(s)`}
              action={
                row?.quadrant && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-2.5 py-1 text-[11px] text-ink-2">
                    <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[row.quadrant]] }} />
                    {QUADRANT_EMOJI[row.quadrant]} {QUADRANT_SHORT[row.quadrant]}
                  </span>
                )
              }
            >
              <ul className="divide-y divide-[color:var(--grid)]">
                {events.map((e) => (
                  <EventLine key={e.id} e={e} />
                ))}
              </ul>
            </Card>
          )
        })}
      </div>
      {byDay.length > limit && (
        <div className="text-center">
          <button onClick={() => setLimit((l) => l + PAGE)} className="rounded-full border border-line px-4 py-2 text-sm hover:bg-surface-2">
            Carregar mais dias ({byDay.length - limit} restantes)
          </button>
        </div>
      )}
    </>
  )
}
