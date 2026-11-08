import { useMemo } from 'react'
import { Chart } from '../components/Chart'
import { Card, Illustration } from '../components/ui'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, FONT, type Option } from '../lib/echarts'
import { longDate, parseDay, shortDate } from '../lib/format'
import type { Habit } from '../types'

const LALLY_MEDIAN = 66

function daysBetween(a: string, b: string) {
  return Math.round((parseDay(b).getTime() - parseDay(a).getTime()) / 86_400_000)
}

function HabitCard({ habit }: { habit: Habit }) {
  const { t, start } = useLife()
  const points = habit.points.filter((p) => p.day >= start)
  const last = habit.points[habit.points.length - 1]
  const age = daysBetween(habit.started, last.day) + 1
  const milestone = new Date(parseDay(habit.started).getTime() + (LALLY_MEDIAN - 1) * 86_400_000).toISOString().slice(0, 10)
  const recent = habit.points.slice(-14)
  const recentRate = recent.filter((p) => p.done).length / recent.length

  const option = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 36, right: 12, top: 14, bottom: 26 },
      xAxis: { type: 'category', data: points.map((p) => p.day), boundaryGap: false, ...axisStyle(t), splitLine: { show: false },
        axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: string) => shortDate(v) } },
      yAxis: { type: 'value', min: 0, max: 100, interval: 50, ...axisStyle(t) },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'line', lineStyle: { color: t.axis } },
        formatter: (ps: { dataIndex: number }[]) => {
          const p = points[ps[0].dataIndex]
          return `<b>${longDate(p.day)}</b><br/>${p.done ? '✓ feito' : '✗ não feito'} · força ${p.strength}/100`
        },
      },
      series: [
        {
          type: 'line',
          data: points.map((p) => p.strength),
          symbol: 'none',
          smooth: 0.2,
          lineStyle: { width: 2, color: t['area-growth'] },
          areaStyle: { color: t['area-growth'], opacity: 0.12 },
          markLine:
            milestone >= (points[0]?.day ?? '') && milestone <= last.day
              ? {
                  silent: true,
                  symbol: 'none',
                  lineStyle: { color: t.axis, type: 'solid' },
                  label: { formatter: '~66 dias', color: t['ink-2'], fontFamily: FONT, fontSize: 10, position: 'insideEndTop' },
                  data: [{ xAxis: milestone }],
                }
              : undefined,
        },
      ],
    }),
    [last.day, milestone, points, t],
  )

  return (
    <Card
      title={habit.habit}
      subtitle={`desde ${longDate(habit.started)} · ${age} dias`}
      action={
        <div className="text-right">
          <div className="text-2xl font-semibold">{last.strength}</div>
          <div className="text-[11px] text-muted">força hoje</div>
        </div>
      }
    >
      <p className="mb-3 rounded-xl bg-surface-2 px-3 py-2 text-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted">Plano se → então</span>
        <br />
        {habit.if_then}
      </p>
      <Chart option={option} height={150} ariaLabel={`Força do hábito ${habit.habit}`} />
      <div className="mt-2" aria-label="Últimos 28 dias">
        <div className="mb-1 text-[11px] text-muted">Últimos 28 dias</div>
        <div className="flex gap-1">
          {habit.points.slice(-28).map((p) => (
            <span
              key={p.day}
              title={`${longDate(p.day)}: ${p.done ? 'feito' : 'não feito'}`}
              className="h-4 flex-1 rounded-sm"
              style={{ background: p.done ? t['area-growth'] : t.grid }}
            />
          ))}
        </div>
      </div>
      <p className="mt-3 text-xs text-ink-2">
        Cumprido em {Math.round(habit.completion * 100)}% dos dias · {Math.round(recentRate * 100)}% nas últimas 2 semanas.
      </p>
    </Card>
  )
}

export function Habits() {
  const { payload } = useLife()
  return (
    <>
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Illustration name="feature-habits" alt="" tile className="h-24 w-24 shrink-0" />
          <div className="space-y-2 text-sm text-ink-2">
            <p>
              <b className="text-ink">Força, não sequência.</b> A curva sobe a cada dia cumprido e cai só um pouco quando você
              falha. Pular um dia isolado não atrapalha a formação do hábito (Lally et al., 2010).
            </p>
            <p>
              <b className="text-ink">~66 dias</b> foi a mediana para um hábito ficar automático, mas variou de 18 a 254 dias entre
              as pessoas. Use como referência, não como prazo.
            </p>
            <p>
              <b className="text-ink">Planos “se → então”</b> (intenções de implementação) aumentam bastante a chance de cumprir um
              objetivo (Gollwitzer &amp; Sheeran, 2006).
            </p>
          </div>
        </div>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
        {payload.habits.map((h) => (
          <HabitCard key={h.habit} habit={h} />
        ))}
      </div>
    </>
  )
}
