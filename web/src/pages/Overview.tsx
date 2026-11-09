import { useMemo } from 'react'
import { Chart } from '../components/Chart'
import { InsightCard } from '../components/InsightCard'
import { SupportCard } from '../components/Support'
import { Card, Illustration, Stat } from '../components/ui'
import { useLife } from '../lib/context'
import { baseOption, type Option } from '../lib/echarts'
import { fmt0, fmt1, hoursDec, longDate, mean, money, signed, sum, timeOf } from '../lib/format'
import { AREA_TOKEN, QUADRANT_EMOJI, QUADRANT_SHORT, QUADRANT_TOKEN } from '../lib/theme'
import { AREA_IMG, AREA_ORDER, SCORE_KEY } from '../lib/areas'
import type { AreaKey } from '../types'

function Ring({ value, color, size = 76 }: { value: number; color: string; size?: number }) {
  const r = size / 2 - 6
  const c = 2 * Math.PI * r
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--grid)" strokeWidth={6} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={6}
        strokeLinecap="round"
        strokeDasharray={`${(c * value) / 100} ${c}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" fill="var(--ink)" fontSize="18" fontWeight="600">
        {Math.round(value)}
      </text>
    </svg>
  )
}

export function Overview() {
  const { payload, days, prevDays, t, go, start } = useLife()

  const weeks = payload.weeks.filter((w) => w.week_start >= (days[0]?.week_start ?? start))
  const latest = days[days.length - 1]
  const latestAffect = payload.affect.filter((a) => a.day === latest?.day)
  const who5 = payload.assessments.filter((a) => a.instrument === 'who5')
  const lastWho5 = who5[who5.length - 1]
  const prevWho5 = who5[who5.length - 2]

  const k = useMemo(() => {
    const m = (key: keyof (typeof days)[number], rows = days) => mean(rows.map((d) => d[key] as number | undefined))
    return {
      sleep: m('sleep_hours'),
      sleepPrev: m('sleep_hours', prevDays),
      se: m('sleep_efficiency'),
      sePrev: m('sleep_efficiency', prevDays),
      valence: m('valence'),
      valencePrev: m('valence', prevDays),
      stress: m('stress'),
      stressPrev: m('stress', prevDays),
      study: sum(days.map((d) => d.study_minutes)) / 60,
      studyPrev: sum(prevDays.map((d) => d.study_minutes)) / 60,
      exerciseDays: days.filter((d) => (d.exercise_minutes ?? 0) > 0).length,
      exercisePrev: prevDays.filter((d) => (d.exercise_minutes ?? 0) > 0).length,
      spend: sum(days.map((d) => d.spend_discretionary)),
      spendPrev: sum(prevDays.map((d) => d.spend_discretionary)),
    }
  }, [days, prevDays])

  const sparkline = (area: AreaKey): Option => ({
    ...baseOption(t),
    grid: { left: 0, right: 0, top: 4, bottom: 0 },
    xAxis: { type: 'category', show: false, data: weeks.map((w) => w.week_start) },
    yAxis: { type: 'value', show: false, min: 0, max: 100 },
    tooltip: {
      ...baseOption(t).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: t.axis } },
      formatter: (p: { name: string; value: number }[]) => `Semana de ${p[0].name.slice(8, 10)}/${p[0].name.slice(5, 7)}: <b>${p[0].value}</b>`,
    },
    series: [
      {
        type: 'line',
        data: weeks.map((w) => w[SCORE_KEY[area]]),
        smooth: 0.3,
        symbol: 'none',
        lineStyle: { width: 2, color: t[AREA_TOKEN[area]] },
        areaStyle: { color: t[AREA_TOKEN[area]], opacity: 0.08 },
      },
    ],
  })

  const delta = (now: number | null, prev: number | null, unit = '', digits = 1) => {
    if (now == null || prev == null) return undefined
    const diff = now - prev
    return Math.abs(diff) < 0.5 * 10 ** -digits ? '≈ igual ao período anterior' : `${signed(diff, digits)}${unit} vs período anterior`
  }
  const better = (now: number | null, prev: number | null, higherIsBetter = true, digits = 1) => {
    if (now == null || prev == null || Math.abs(now - prev) < 0.5 * 10 ** -digits) return undefined
    return higherIsBetter ? now > prev : now < prev
  }
  // one insight per condition keeps the overview varied
  const topInsights = payload.insights.filter((i, idx, all) => all.findIndex((j) => j.x === i.x) === idx).slice(0, 4)

  return (
    <>
      {payload.support.highlight && <SupportCard />}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {AREA_ORDER.map((area) => {
          const score = mean(days.map((d) => d[SCORE_KEY[area]])) ?? 0
          const prev = mean(prevDays.map((d) => d[SCORE_KEY[area]]))
          const color = t[AREA_TOKEN[area]]
          return (
            <button
              key={area}
              onClick={() => go('areas')}
              className="card group text-left transition hover:border-[color:var(--axis)]"
            >
              <div className="flex items-center gap-4">
                <Ring value={score} color={color} />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-sm font-semibold">
                    <span aria-hidden>{payload.areas[area].emoji}</span>
                    {payload.areas[area].label}
                  </div>
                  <div className="text-xs text-muted">índice 0–100 no período</div>
                  {prev != null && (
                    <div className={`mt-1 text-xs ${Math.abs(score - prev) < 0.5 ? 'text-muted' : score > prev ? 'text-good-text' : 'text-critical'}`}>
                      {Math.abs(score - prev) < 0.5 ? '≈ igual ao anterior' : `${score > prev ? '▲' : '▼'} ${signed(score - prev, 0)} vs anterior`}
                    </div>
                  )}
                </div>
                <Illustration name={AREA_IMG[area]} alt="" className="ml-auto hidden h-14 w-14 sm:block" />
              </div>
              <Chart option={sparkline(area)} height={44} className="mt-3" ariaLabel={`Índice semanal de ${payload.areas[area].label}`} />
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Sono médio" value={hoursDec(k.sleep)} accent={t['area-body']}
          delta={delta(k.sleep, k.sleepPrev, ' h')} deltaGood={better(k.sleep, k.sleepPrev)} />
        <Stat label="Eficiência do sono" value={fmt0(k.se)} unit="%" accent={t['area-body']}
          hint="Tempo dormindo ÷ tempo na cama (Consensus Sleep Diary). Acima de 85% é a referência usual."
          delta={delta(k.se, k.sePrev, ' p.p.')} deltaGood={better(k.se, k.sePrev)} />
        <Stat label="Valência média" value={signed(k.valence)} unit="de −2 a +2" accent={t['area-mind']}
          hint="Quão agradável você se sentiu, em média, nos check-ins (modelo circumplexo de Russell)."
          delta={delta(k.valence, k.valencePrev)} deltaGood={better(k.valence, k.valencePrev)} />
        <Stat label="Estresse médio" value={fmt1(k.stress)} unit="/5" accent={t['area-mind']}
          delta={delta(k.stress, k.stressPrev)} deltaGood={better(k.stress, k.stressPrev, false)} />
        <Stat label="Estudo" value={fmt0(k.study)} unit="h" accent={t['area-growth']}
          delta={delta(k.study, k.studyPrev, ' h', 0)} deltaGood={better(k.study, k.studyPrev, true, 0)} />
        <Stat label="Dias com treino" value={String(k.exerciseDays)} unit={`de ${days.length}`} accent={t['area-body']}
          delta={delta(k.exerciseDays, k.exercisePrev, '', 0)} deltaGood={better(k.exerciseDays, k.exercisePrev, true, 0)} />
        <Stat label="Gasto variável" value={money(k.spend)} accent={t['area-money']}
          hint="Sem aluguel, contas e assinaturas."
          delta={k.spendPrev ? `${k.spend > k.spendPrev ? '+' : '−'}${money(Math.abs(k.spend - k.spendPrev))} vs anterior` : undefined}
          deltaGood={k.spendPrev ? better(k.spend, k.spendPrev, false, 0) : undefined} />
        <Stat label="Bem-estar (WHO-5)" value={lastWho5 ? fmt0(lastWho5.score) : '—'} unit="/100" accent={t['area-mind']}
          hint="Índice de Bem-Estar da OMS, respondido aos domingos. Não é diagnóstico."
          delta={lastWho5 && prevWho5 ? `${signed(lastWho5.score - prevWho5.score, 0)} vs semana anterior` : undefined}
          deltaGood={lastWho5 && prevWho5 ? better(lastWho5.score, prevWho5.score, true, 0) : undefined} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
        {latest && (
          <Card title={`Último dia · ${longDate(latest.day)}`} subtitle="O que você registrou">
            <div className="space-y-3 text-sm">
              <div className="flex flex-wrap gap-2">
                {latest.quadrant && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-3 py-1 text-xs">
                    <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[latest.quadrant]] }} />
                    {QUADRANT_EMOJI[latest.quadrant]} {QUADRANT_SHORT[latest.quadrant]}
                  </span>
                )}
                {latest.sleep_hours != null && (
                  <span className="rounded-full bg-surface-2 px-3 py-1 text-xs">
                    😴 {hoursDec(latest.sleep_hours)} · {latest.bedtime}→{latest.wake_time}
                  </span>
                )}
                {latest.study_minutes ? (
                  <span className="rounded-full bg-surface-2 px-3 py-1 text-xs">📚 {latest.study_minutes} min de {latest.study_topics}</span>
                ) : null}
                {latest.exercise_kinds && (
                  <span className="rounded-full bg-surface-2 px-3 py-1 text-xs">🏃 {latest.exercise_kinds}</span>
                )}
              </div>
              <ul className="space-y-1.5">
                {latestAffect.map((a) => (
                  <li key={a.ts} className="flex items-center gap-2">
                    <span className="tnum w-11 text-xs text-muted">{timeOf(a.ts)}</span>
                    <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[a.quadrant]] }} aria-hidden />
                    <span>{a.emotions?.join(', ')}</span>
                  </li>
                ))}
              </ul>
              {latest.autonomy != null && (
                <p className="text-xs text-ink-2">
                  Necessidades: autonomia {latest.autonomy}/5 · competência {latest.competence}/5 · vínculo{' '}
                  {latest.relatedness}/5
                </p>
              )}
            </div>
          </Card>
        )}
        <Card
          title="O que os seus dados sugerem"
          subtitle="Associações dentro de você mesmo — não causas"
          action={
            <button className="text-xs text-ink-2 underline" onClick={() => go('patterns')}>
              ver todos ({payload.insights.length})
            </button>
          }
        >
          <div className="space-y-2">
            {topInsights.length === 0 && (
              <p className="text-sm text-ink-2">
                Os padrões aparecem depois de algumas semanas de registro: cada dia precisa ser comparado com a sua própria média.
              </p>
            )}
            {topInsights.map((i) => (
              <InsightCard key={i.id} insight={i} compact />
            ))}
          </div>
        </Card>
      </div>

      <Card title="Atalhos">
        <div className="flex flex-wrap gap-2 text-sm">
          {(
            [
              ['tracks', '≋ Ver os trilhos'],
              ['emotions', '◐ Mapa das emoções'],
              ['habits', '↗ Hábitos'],
              ['week', '☰ Relatório da semana'],
            ] as const
          ).map(([key, label]) => (
            <button key={key} onClick={() => go(key)} className="rounded-full border border-line px-3 py-1.5 hover:bg-surface-2">
              {label}
            </button>
          ))}
        </div>
      </Card>
    </>
  )
}
