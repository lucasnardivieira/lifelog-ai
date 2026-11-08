import { useMemo, useState } from 'react'
import { Chart } from '../components/Chart'
import { DayDetail } from '../components/DayDetail'
import { Card, Chip, Note } from '../components/ui'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, FONT, type Option } from '../lib/echarts'
import { fmt0, fmt1, longDate, mean, money } from '../lib/format'
import { QUADRANT_SHORT, QUADRANT_TOKEN, type Tokens } from '../lib/theme'
import type { Day } from '../types'

interface Metric {
  key: string
  label: string
  value: (d: Day) => number | null | undefined
  format: (v: number) => string
  scale: 'sequential' | 'diverging' | 'quadrant'
  min?: number
  max?: number
  hint: string
}

const QUAD_INDEX = { yellow: 0, red: 1, blue: 2, green: 3 } as const
const QUAD_KEYS = ['yellow', 'red', 'blue', 'green'] as const

const METRICS: Metric[] = [
  { key: 'valence', label: 'Valência', value: (d) => d.valence, format: (v) => fmt1(v), scale: 'diverging', min: -2, max: 2,
    hint: 'Quão agradável foi o dia (−2 a +2). Vermelho = desagradável, azul = agradável.' },
  { key: 'quadrant', label: 'Quadrante', value: (d) => (d.quadrant ? QUAD_INDEX[d.quadrant] : null), format: (v) => QUADRANT_SHORT[QUAD_KEYS[v]],
    scale: 'quadrant', hint: 'O quadrante emocional predominante do dia.' },
  { key: 'sleep', label: 'Sono', value: (d) => d.sleep_hours, format: (v) => `${fmt1(v)} h`, scale: 'sequential', min: 5, max: 9.5,
    hint: 'Horas dormidas (Consensus Sleep Diary).' },
  { key: 'efficiency', label: 'Eficiência do sono', value: (d) => d.sleep_efficiency, format: (v) => `${fmt0(v)}%`, scale: 'sequential', min: 75, max: 98,
    hint: 'Tempo dormindo ÷ tempo na cama.' },
  { key: 'stress', label: 'Estresse', value: (d) => d.stress, format: (v) => `${fmt1(v)}/5`, scale: 'sequential', min: 1, max: 5,
    hint: 'Estresse percebido no dia (1–5).' },
  { key: 'study', label: 'Estudo', value: (d) => d.study_minutes, format: (v) => `${fmt0(v)} min`, scale: 'sequential', min: 0, max: 150,
    hint: 'Minutos de estudo.' },
  { key: 'exercise', label: 'Exercício', value: (d) => d.exercise_minutes, format: (v) => `${fmt0(v)} min`, scale: 'sequential', min: 0, max: 80,
    hint: 'Minutos de exercício.' },
  { key: 'habits', label: 'Hábitos', value: (d) => (d.habits_tracked ? (100 * (d.habits_done ?? 0)) / d.habits_tracked : null),
    format: (v) => `${fmt0(v)}%`, scale: 'sequential', min: 0, max: 100, hint: 'Percentual de hábitos cumpridos.' },
  { key: 'spend', label: 'Gasto variável', value: (d) => d.spend_discretionary, format: (v) => money(v), scale: 'sequential', min: 0, max: 400,
    hint: 'Gastos sem aluguel, contas e assinaturas.' },
]

const WEEKDAY_LABELS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']

function visualMap(metric: Metric, t: Tokens): Option {
  if (metric.scale === 'quadrant') {
    return {
      type: 'piecewise',
      show: false,
      pieces: QUAD_KEYS.map((q, i) => ({ value: i, color: t[QUADRANT_TOKEN[q]] })),
    }
  }
  const colors =
    metric.scale === 'diverging'
      ? [t['div-neg'], t['div-mid'], t['div-pos']]
      : [t['seq-1'], t['seq-2'], t['seq-3'], t['seq-4'], t['seq-5'], t['seq-6'], t['seq-7']]
  return {
    type: 'continuous',
    min: metric.min,
    max: metric.max,
    orient: 'horizontal',
    left: 'center',
    bottom: 0,
    itemWidth: 12,
    itemHeight: 180,
    calculable: false,
    text: [metric.format(metric.max ?? 0), metric.format(metric.min ?? 0)],
    textStyle: { color: t.muted, fontSize: 11, fontFamily: FONT },
    inRange: { color: colors },
  }
}

export function CalendarPage() {
  const { days, t } = useLife()
  const [metricKey, setMetricKey] = useState('valence')
  const [selected, setSelected] = useState<string | null>(null)
  const metric = METRICS.find((m) => m.key === metricKey)!

  const data = useMemo(
    () => days.map((d) => [d.day, metric.value(d) ?? null] as [string, number | null]).filter((x) => x[1] != null),
    [days, metric],
  )

  const option = useMemo<Option>(
    () => ({
      ...baseOption(t),
      tooltip: {
        ...baseOption(t).tooltip,
        formatter: (p: { value: [string, number] }) => `<b>${longDate(p.value[0])}</b><br/>${metric.label}: ${metric.format(p.value[1])}`,
      },
      visualMap: visualMap(metric, t),
      calendar: {
        top: 28,
        left: 36,
        right: 12,
        bottom: metric.scale === 'quadrant' ? 8 : 44,
        cellSize: ['auto', 18],
        range: [days[0].day, days[days.length - 1].day],
        firstDay: 0,
        orient: 'horizontal',
        itemStyle: { color: t.surface, borderColor: t.surface, borderWidth: 3 },
        splitLine: { show: false },
        dayLabel: { color: t.muted, fontSize: 10, nameMap: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'], fontFamily: FONT },
        monthLabel: {
          color: t['ink-2'],
          fontSize: 11,
          fontFamily: FONT,
          nameMap: ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'],
        },
        yearLabel: { show: false },
      },
      series: [
        {
          type: 'heatmap',
          coordinateSystem: 'calendar',
          data,
          itemStyle: { borderRadius: 4 },
        },
      ],
    }),
    [data, days, metric, t],
  )

  const byWeekday = useMemo(() => {
    const groups: number[][] = Array.from({ length: 7 }, () => [])
    days.forEach((d) => {
      const v = metric.value(d)
      if (v != null) groups[d.iso_weekday - 1].push(v)
    })
    return groups.map((g) => mean(g))
  }, [days, metric])

  const weekdayOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 48, right: 12, top: 12, bottom: 28 },
      xAxis: { type: 'category', data: WEEKDAY_LABELS, ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', ...axisStyle(t), axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: number) => metric.format(v) } },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: t.grid, opacity: 0.4 } },
        formatter: (p: { name: string; value: number }[]) => `${p[0].name}: <b>${metric.format(p[0].value)}</b> (média)`,
      },
      series: [
        {
          type: 'bar',
          data: byWeekday,
          barWidth: '45%',
          itemStyle: { color: t['seq-5'], borderRadius: [4, 4, 0, 0] },
        },
      ],
    }),
    [byWeekday, metric, t],
  )

  return (
    <>
      <Card title="Escolha o que pintar no calendário" subtitle={metric.hint}>
        <div className="flex flex-wrap gap-2">
          {METRICS.map((m) => (
            <Chip key={m.key} active={m.key === metricKey} onClick={() => setMetricKey(m.key)}>
              {m.label}
            </Chip>
          ))}
        </div>
      </Card>
      <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card title={metric.label} subtitle="Cada quadrado é um dia · clique para abrir">
          <div className="overflow-x-auto">
            <div className="min-w-[640px]">
              <Chart
                option={option}
                height={metric.scale === 'quadrant' ? 190 : 230}
                ariaLabel={`Calendário de ${metric.label}`}
                onClick={(p) => setSelected((p.data as [string, number])[0])}
              />
            </div>
          </div>
          {metric.scale === 'quadrant' && (
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
              {QUAD_KEYS.map((q) => (
                <li key={q} className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: t[QUADRANT_TOKEN[q]] }} />
                  {QUADRANT_SHORT[q]}
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Por dia da semana" subtitle={`Média de ${metric.label.toLowerCase()} em cada dia da semana`}>
          {metric.scale === 'quadrant' ? (
            <Note>Escolha uma métrica numérica para ver o padrão semanal.</Note>
          ) : (
            <Chart option={weekdayOption} height={230} ariaLabel={`Média de ${metric.label} por dia da semana`} />
          )}
        </Card>
      </div>
      {selected && <DayDetail day={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
