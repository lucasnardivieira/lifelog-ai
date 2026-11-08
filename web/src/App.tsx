import { useEffect, useMemo, useState } from 'react'
import { SupportDialog } from './components/Support'
import { Segmented } from './components/ui'
import { LifeContext, type Life, type PageKey } from './lib/context'
import { loadPayload } from './lib/data'
import { PERIODS, periodStart, previousWindow, type Period } from './lib/period'
import { getThemeChoice, setThemeChoice, useTokens, type ThemeChoice } from './lib/theme'
import { Areas } from './pages/Areas'
import { CalendarPage } from './pages/Calendar'
import { Diary } from './pages/Diary'
import { Emotions } from './pages/Emotions'
import { Habits } from './pages/Habits'
import { Overview } from './pages/Overview'
import { Patterns } from './pages/Patterns'
import { Tracks } from './pages/Tracks'
import { WeekPage } from './pages/Week'
import { Wellbeing } from './pages/Wellbeing'
import type { Payload } from './types'

const PAGES: { key: PageKey; label: string; icon: string; title: string }[] = [
  { key: 'overview', label: 'Visão geral', icon: '◎', title: 'Visão geral' },
  { key: 'tracks', label: 'Trilhos', icon: '≋', title: 'Os trilhos da sua vida' },
  { key: 'calendar', label: 'Calendário', icon: '▦', title: 'Calendário' },
  { key: 'emotions', label: 'Emoções', icon: '◐', title: 'Emoções' },
  { key: 'wellbeing', label: 'Bem-estar', icon: '♡', title: 'Bem-estar' },
  { key: 'habits', label: 'Hábitos', icon: '↗', title: 'Hábitos' },
  { key: 'areas', label: 'Áreas', icon: '◇', title: 'Áreas da vida' },
  { key: 'patterns', label: 'Padrões', icon: '⟡', title: 'Padrões' },
  { key: 'diary', label: 'Diário', icon: '✎', title: 'Diário' },
  { key: 'week', label: 'Semana', icon: '☰', title: 'Relatório da semana' },
]

const THEMES: { key: ThemeChoice; label: string }[] = [
  { key: 'system', label: 'Auto' },
  { key: 'light', label: 'Claro' },
  { key: 'dark', label: 'Escuro' },
]

const readHash = (): PageKey => {
  const k = location.hash.slice(1) as PageKey
  return PAGES.some((p) => p.key === k) ? k : 'overview'
}

export default function App() {
  const [payload, setPayload] = useState<Payload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState<PageKey>(readHash)
  const [period, setPeriod] = useState<Period>('90')
  const [theme, setTheme] = useState<ThemeChoice>(getThemeChoice)
  const [supportOpen, setSupportOpen] = useState(false)
  const t = useTokens()

  useEffect(() => {
    loadPayload().then(setPayload, (e: Error) => setError(e.message))
    const onHash = () => setPage(readHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const go = (key: PageKey) => {
    location.hash = key
    window.scrollTo({ top: 0 })
  }

  const life = useMemo<Life | null>(() => {
    if (!payload) return null
    const start = periodStart(payload, period)
    return {
      payload,
      period,
      start,
      days: payload.days.filter((d) => d.day >= start),
      prevDays: previousWindow(payload.days, start),
      t,
      openSupport: () => setSupportOpen(true),
      go,
    }
  }, [payload, period, t])

  if (error) return <p className="m-8 text-critical">{error}</p>
  if (!life) return <div className="m-auto mt-32 h-8 w-8 animate-spin rounded-full border-2 border-line border-t-ink" />

  const current = PAGES.find((p) => p.key === page)!
  return (
    <LifeContext.Provider value={life}>
      <div className="mx-auto flex min-h-dvh max-w-[1400px]">
        <nav
          aria-label="Seções"
          className="sticky top-0 hidden h-dvh w-56 shrink-0 flex-col gap-1 border-r border-line px-3 py-5 lg:flex"
        >
          <div className="mb-4 px-3">
            <div className="text-lg font-bold tracking-tight">Trilhos</div>
            <div className="text-xs text-muted">lifelog · {life.payload.sample ? 'demo' : 'privado'}</div>
          </div>
          {PAGES.map((p) => (
            <a
              key={p.key}
              href={`#${p.key}`}
              aria-current={page === p.key ? 'page' : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                page === p.key ? 'bg-surface-2 font-semibold text-ink' : 'text-ink-2 hover:bg-surface-2'
              }`}
            >
              <span aria-hidden className="w-4 text-center text-muted">{p.icon}</span>
              {p.label}
            </a>
          ))}
          <button
            onClick={() => setSupportOpen(true)}
            className={`mt-auto rounded-xl border px-3 py-2 text-left text-sm ${
              life.payload.support.highlight ? 'border-serious text-ink' : 'border-line text-ink-2'
            } hover:bg-surface-2`}
          >
            💬 Precisa conversar?
            <span className="block text-xs text-muted">CVV 188 · grátis, 24h</span>
          </button>
        </nav>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-10 border-b border-line bg-page/90 backdrop-blur">
            <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
              <h1 className="mr-auto text-lg font-semibold tracking-tight sm:text-xl">{current.title}</h1>
              <Segmented label="Período" value={period} options={PERIODS} onChange={setPeriod} />
              <Segmented
                label="Tema"
                value={theme}
                options={THEMES}
                onChange={(v) => {
                  setTheme(v)
                  setThemeChoice(v)
                }}
              />
              <button
                onClick={() => setSupportOpen(true)}
                className="rounded-full border border-line px-3 py-1 text-xs text-ink-2 hover:bg-surface-2 lg:hidden"
              >
                💬 Conversar
              </button>
            </div>
            <nav aria-label="Seções" className="flex gap-1 overflow-x-auto px-4 pb-2 lg:hidden">
              {PAGES.map((p) => (
                <a
                  key={p.key}
                  href={`#${p.key}`}
                  aria-current={page === p.key ? 'page' : undefined}
                  className={`shrink-0 rounded-full px-3 py-1 text-xs ${
                    page === p.key ? 'bg-ink text-page' : 'text-ink-2'
                  }`}
                >
                  {p.label}
                </a>
              ))}
            </nav>
          </header>

          {life.payload.sample && (
            <div className="mx-4 mt-4 rounded-xl border border-line bg-surface-2 px-4 py-2 text-xs text-ink-2 sm:mx-6">
              🧪 <strong>Demonstração com dados fictícios</strong> gerados com padrões realistas. Seus dados reais
              ficam só no seu computador.
            </div>
          )}

          <main className="space-y-4 px-4 py-4 sm:px-6 sm:py-6">
            {page === 'overview' && <Overview />}
            {page === 'tracks' && <Tracks />}
            {page === 'calendar' && <CalendarPage />}
            {page === 'emotions' && <Emotions />}
            {page === 'wellbeing' && <Wellbeing />}
            {page === 'habits' && <Habits />}
            {page === 'areas' && <Areas />}
            {page === 'patterns' && <Patterns />}
            {page === 'diary' && <Diary />}
            {page === 'week' && <WeekPage />}
          </main>

          <footer className="px-6 pb-8 text-xs text-muted">
            Não é uma ferramenta de diagnóstico. Fundamentação:{' '}
            <a
              className="underline"
              href="https://github.com/lucasnardivieira/lifelog-ai/blob/main/docs/research/psychology-foundations.md"
            >
              bases da psicologia
            </a>
            . Atualizado em {new Date(life.payload.generated_at).toLocaleString('pt-BR')}.
          </footer>
        </div>
      </div>
      <SupportDialog open={supportOpen} onClose={() => setSupportOpen(false)} />
    </LifeContext.Provider>
  )
}
