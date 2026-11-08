import { useMemo, useState } from 'react'
import { Chart } from '../components/Chart'
import { SupportCard } from '../components/Support'
import { Card, Illustration, Legend, Stat } from '../components/ui'
import { AREA_ORDER, SCORE_KEY } from '../lib/areas'
import { useLife } from '../lib/context'
import { baseOption, FONT, type Option } from '../lib/echarts'
import { fmt0, fmt1, hoursDec, longDate, money, shortDate, signed, weekday } from '../lib/format'
import { AREA_TOKEN, QUADRANT_SHORT, QUADRANT_TOKEN } from '../lib/theme'
import type { Week } from '../types'

const QUADS = ['yellow', 'red', 'blue', 'green'] as const

function compare(cur: number | undefined, prev: number | undefined, higherIsBetter: boolean, digits = 1, unit = '') {
  if (cur == null || prev == null) return { delta: undefined, good: undefined }
  const d = cur - prev
  if (Math.abs(d) < 0.5 * 10 ** -digits) return { delta: '≈ igual à semana anterior', good: undefined }
  return { delta: `${signed(d, digits)}${unit} vs semana anterior`, good: higherIsBetter ? d > 0 : d < 0 }
}

export function WeekPage() {
  const { payload, t, go } = useLife()
  const weeks = payload.weeks.filter((w) => w.days === 7)
  const [idx, setIdx] = useState(weeks.length - 1)
  const w: Week = weeks[idx]
  const p: Week | undefined = weeks[idx - 1]
  const end = new Date(`${w.week_start}T12:00:00`)
  end.setDate(end.getDate() + 6)
  const endIso = end.toISOString().slice(0, 10)
  const days = payload.days.filter((d) => d.day >= w.week_start && d.day <= endIso)
  const best = [...days].sort((a, b) => b.mind_score - a.mind_score)[0]
  const hardest = [...days].sort((a, b) => a.mind_score - b.mind_score)[0]
  const habits = payload.habits.map((h) => {
    const pts = h.points.filter((x) => x.day >= w.week_start && x.day <= endIso)
    return { habit: h.habit, done: pts.filter((x) => x.done).length, total: pts.length }
  }).filter((h) => h.total)
  const gratitude = payload.events.filter((e) => e.type === 'gratitude' && e.day >= w.week_start && e.day <= endIso)
  const improved = p ? AREA_ORDER.filter((a) => w[SCORE_KEY[a]] > p[SCORE_KEY[a]]).length : 0

  const scoresOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 130, right: 40, top: 4, bottom: 4 },
      xAxis: { type: 'value', min: 0, max: 100, show: false },
      yAxis: {
        type: 'category',
        inverse: true,
        data: AREA_ORDER.map((a) => `${payload.areas[a].emoji} ${payload.areas[a].label}`),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: t['ink-2'], fontFamily: FONT, fontSize: 12 },
      },
      tooltip: { ...baseOption(t).tooltip, trigger: 'item' },
      series: [
        {
          type: 'bar',
          barWidth: 12,
          data: AREA_ORDER.map((a) => ({ value: w[SCORE_KEY[a]], itemStyle: { color: t[AREA_TOKEN[a]], borderRadius: [0, 4, 4, 0] } })),
          label: { show: true, position: 'right', color: t['ink-2'], fontFamily: FONT, formatter: (x: { value: number }) => `${x.value}` },
        },
        ...(p
          ? [
              {
                type: 'scatter',
                name: 'semana anterior',
                symbol: 'rect',
                symbolSize: [2, 18],
                data: AREA_ORDER.map((a) => p[SCORE_KEY[a]]),
                itemStyle: { color: t.ink },
                tooltip: { formatter: (x: { value: number }) => `semana anterior: ${x.value}` },
              },
            ]
          : []),
      ],
    }),
    [p, payload.areas, t, w],
  )

  const quadOption: Option = {
    ...baseOption(t),
    grid: { left: 0, right: 0, top: 0, bottom: 0 },
    xAxis: { type: 'value', max: 7, show: false },
    yAxis: { type: 'category', data: [''], show: false },
    tooltip: { ...baseOption(t).tooltip, trigger: 'item', formatter: (x: { seriesName: string; value: number }) => `${x.seriesName}: ${x.value} dia(s)` },
    series: QUADS.map((q) => ({
      name: QUADRANT_SHORT[q],
      type: 'bar',
      stack: 'q',
      barWidth: 22,
      data: [w[`days_${q}`]],
      itemStyle: { color: t[QUADRANT_TOKEN[q]], borderColor: t.surface, borderWidth: 2 },
    })),
  }

  const sleep = compare(w.avg_sleep_hours, p?.avg_sleep_hours, true)
  const valence = compare(w.avg_valence, p?.avg_valence, true, 2)
  const stress = compare(w.avg_stress, p?.avg_stress, false)
  const study = compare(w.study_minutes / 60, p ? p.study_minutes / 60 : undefined, true, 0, ' h')
  const lowWho5 = w.who5_score != null && w.who5_score < 52

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <button disabled={idx === 0} onClick={() => setIdx((i) => i - 1)} className="rounded-full border border-line px-3 py-1 text-sm disabled:opacity-40" aria-label="Semana anterior">
          ←
        </button>
        <div className="text-sm font-semibold">
          {shortDate(w.week_start)} – {shortDate(endIso)}
          {w.has_deadline && <span className="ml-2 rounded-full bg-surface-2 px-2 py-0.5 text-xs font-normal">⏳ semana com prazo</span>}
        </div>
        <button disabled={idx === weeks.length - 1} onClick={() => setIdx((i) => i + 1)} className="rounded-full border border-line px-3 py-1 text-sm disabled:opacity-40" aria-label="Próxima semana">
          →
        </button>
      </div>

      {lowWho5 && <SupportCard />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Sono médio" value={hoursDec(w.avg_sleep_hours)} accent={t['area-body']} delta={sleep.delta} deltaGood={sleep.good} />
        <Stat label="Valência média" value={signed(w.avg_valence ?? null, 2)} unit="−2 a +2" accent={t['area-mind']} delta={valence.delta} deltaGood={valence.good} />
        <Stat label="Estresse médio" value={fmt1(w.avg_stress)} unit="/5" accent={t['area-mind']} delta={stress.delta} deltaGood={stress.good} />
        <Stat label="Estudo" value={fmt0(w.study_minutes / 60)} unit="h" accent={t['area-growth']} delta={study.delta} deltaGood={study.good} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
        <Card title="Índice de cada área" subtitle={p ? 'Barra = esta semana · traço = semana anterior' : 'Esta semana'}>
          <Chart option={scoresOption} height={150} ariaLabel="Índices por área nesta semana e na anterior" />
          <div className="mt-4">
            <div className="mb-1 text-xs text-ink-2">Dias em cada quadrante emocional</div>
            <Chart option={quadOption} height={24} ariaLabel="Dias por quadrante emocional" />
            <div className="mt-2">
              <Legend items={QUADS.map((q) => ({ label: `${QUADRANT_SHORT[q]} (${w[`days_${q}`]})`, color: t[QUADRANT_TOKEN[q]] }))} />
            </div>
          </div>
        </Card>
        <Card
          title="Destaques"
          action={improved >= 3 ? <Illustration name="celebrate" alt="" tile className="h-14 w-14" /> : undefined}
        >
          <ul className="space-y-2 text-sm">
            {improved >= 3 && <li>🎉 {improved} de 4 áreas melhoraram em relação à semana anterior.</li>}
            {best && <li>🌟 Melhor dia: <b>{weekday(best.day)}</b> ({longDate(best.day)}).</li>}
            {hardest && hardest.day !== best?.day && <li>🌧️ Dia mais difícil: <b>{weekday(hardest.day)}</b>, com estresse {fmt1(hardest.stress)}/5.</li>}
            <li>🏃 {w.exercise_days} dia(s) com treino · 📖 {w.reading_pages} páginas · 👥 {w.social_count} programa(s) social(is).</li>
            <li>💸 {money(w.spend_discretionary)} em gastos variáveis.</li>
            {w.who5_score != null && <li>♡ WHO-5 de domingo: <b>{w.who5_score}</b>/100{lowWho5 ? ' (abaixo da referência)' : ''}.</li>}
            {w.distinct_emotions != null && <li>◐ Você usou {w.distinct_emotions} palavras diferentes para descrever o que sentiu.</li>}
            {habits.map((h) => (
              <li key={h.habit}>↗ {h.habit}: {h.done}/{h.total} dias</li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Gratidão da semana">
          {gratitude.length ? (
            <ul className="space-y-1 text-sm italic">
              {gratitude.map((g) => (
                <li key={g.id}>🙏 {g.note}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-2">Nenhuma anotação de gratidão nesta semana. Uma vez por semana já ajuda.</p>
          )}
        </Card>
        <Card title="Reflexão de domingo" subtitle="Diário estruturado: concreto e com fim, para não virar ruminação">
          <ol className="list-inside list-decimal space-y-1 text-sm text-ink-2">
            <li>O que aconteceu de mais marcante nesta semana?</li>
            <li>O que eu senti? (tente uma palavra precisa)</li>
            <li>Qual é um próximo passo pequeno para a semana que vem?</li>
          </ol>
          <button onClick={() => go('patterns')} className="mt-3 text-xs text-ink-2 underline">
            ver padrões que podem ajudar a escolher o próximo passo
          </button>
        </Card>
      </div>
    </>
  )
}
