import { useMemo, useState } from 'react'
import { Chart } from '../components/Chart'
import { DayDetail } from '../components/DayDetail'
import { Card, Legend, Note } from '../components/ui'
import { useLife } from '../lib/context'
import { FONT, baseOption, dot, type Option } from '../lib/echarts'
import { fmt1, hoursDec, longDate, money, shortDate } from '../lib/format'
import { QUADRANT_SHORT, QUADRANT_TOKEN, type Token } from '../lib/theme'
import type { Day } from '../types'

interface Lane {
  key: string
  label: string
  token: Token
  kind: 'bar' | 'line' | 'affect' | 'dot'
  value: (d: Day) => number | null | undefined
  min?: number
  max?: number
}

const LANES: Lane[] = [
  { key: 'sleep', label: '😴 Sono (h)', token: 'area-body', kind: 'bar', value: (d) => d.sleep_hours, min: 4, max: 10 },
  { key: 'affect', label: '◐ Afeto', token: 'q-green', kind: 'affect', value: (d) => d.valence, min: -2, max: 2 },
  { key: 'energy', label: '⚡ Energia', token: 'area-body', kind: 'line', value: (d) => d.energy, min: 1, max: 5 },
  { key: 'stress', label: '🌡️ Estresse', token: 'area-mind', kind: 'line', value: (d) => d.stress, min: 1, max: 5 },
  {
    key: 'needs',
    label: '△ Necessidades',
    token: 'area-mind',
    kind: 'line',
    value: (d) => (d.autonomy == null ? null : ((d.autonomy ?? 0) + (d.competence ?? 0) + (d.relatedness ?? 0)) / 3),
    min: 1,
    max: 5,
  },
  { key: 'exercise', label: '🏃 Exercício (min)', token: 'area-body', kind: 'bar', value: (d) => d.exercise_minutes || null, min: 0 },
  { key: 'study', label: '📚 Estudo (min)', token: 'area-growth', kind: 'bar', value: (d) => d.study_minutes || null, min: 0 },
  {
    key: 'habits',
    label: '↗ Hábitos (%)',
    token: 'area-growth',
    kind: 'bar',
    value: (d) => (d.habits_tracked ? Math.round((100 * (d.habits_done ?? 0)) / d.habits_tracked) : null),
    min: 0,
    max: 100,
  },
  { key: 'spend', label: '💸 Gasto variável', token: 'area-money', kind: 'bar', value: (d) => d.spend_discretionary || null, min: 0 },
  { key: 'social', label: '👥 Social', token: 'area-money', kind: 'dot', value: (d) => (d.social_count ? 1 : null), min: 0, max: 2 },
]

const LANE_H = 46
const GAP = 10
const TOP = 8
const LEFT = 150

function deadlineRanges(days: Day[]): [string, string][] {
  const ranges: [string, string][] = []
  let start: string | null = null
  days.forEach((d, i) => {
    if (d.is_deadline && !start) start = d.day
    const next = days[i + 1]
    if (start && (!next || !next.is_deadline) && d.is_deadline) {
      ranges.push([start, d.day])
      start = null
    }
  })
  return ranges
}

export function Tracks() {
  const { days, t } = useLife()
  const [selected, setSelected] = useState<string | null>(null)
  const dates = days.map((d) => d.day)

  const option = useMemo<Option>(() => {
    const deadlines = deadlineRanges(days)
    const grids = LANES.map((_, i) => ({ left: LEFT, right: 16, top: TOP + i * (LANE_H + GAP), height: LANE_H }))
    const bottomLane = LANES.length - 1
    const xAxes = LANES.map((_, i) => ({
      type: 'category',
      gridIndex: i,
      data: dates,
      boundaryGap: true,
      axisLine: { show: i === bottomLane, lineStyle: { color: t.axis } },
      axisTick: { show: false },
      axisLabel: {
        show: i === bottomLane,
        color: t.muted,
        fontSize: 11,
        formatter: (v: string) => shortDate(v),
      },
    }))
    const yAxes = LANES.map((lane, i) => ({
      type: 'value',
      gridIndex: i,
      min: lane.min,
      max: lane.max,
      name: lane.label,
      nameLocation: 'middle',
      nameRotate: 0,
      nameGap: LEFT - 16,
      nameTextStyle: { color: t['ink-2'], fontSize: 12, fontFamily: FONT, align: 'left' },
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: lane.kind === 'affect', lineStyle: { color: t.grid } },
      splitNumber: 1,
    }))
    const markArea = {
      silent: true,
      itemStyle: { color: t.dark ? 'rgba(255,255,255,0.05)' : 'rgba(11,11,11,0.05)' },
      data: deadlines.map(([a, b]) => [{ xAxis: a }, { xAxis: b }]),
    }
    const series = LANES.map((lane, i) => {
      const color = t[lane.token]
      const data = days.map((d) => lane.value(d) ?? null)
      if (lane.kind === 'affect') {
        return {
          name: lane.label,
          type: 'bar',
          xAxisIndex: i,
          yAxisIndex: i,
          barCategoryGap: '20%',
          markArea,
          data: days.map((d) =>
            d.valence == null
              ? null
              : { value: d.valence, itemStyle: { color: t[QUADRANT_TOKEN[d.quadrant ?? 'green']], borderRadius: d.valence >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] } },
          ),
        }
      }
      if (lane.kind === 'line') {
        return {
          name: lane.label,
          type: 'line',
          xAxisIndex: i,
          yAxisIndex: i,
          data,
          symbol: 'none',
          smooth: 0.25,
          connectNulls: true,
          markArea,
          lineStyle: { width: 2, color },
          areaStyle: { color, opacity: 0.1 },
        }
      }
      if (lane.kind === 'dot') {
        return {
          name: lane.label,
          type: 'scatter',
          xAxisIndex: i,
          yAxisIndex: i,
          data,
          markArea,
          symbolSize: 8,
          itemStyle: { color, borderColor: t.surface, borderWidth: 2 },
        }
      }
      return {
        name: lane.label,
        type: 'bar',
        xAxisIndex: i,
        yAxisIndex: i,
        data,
        barCategoryGap: '20%',
        markArea,
        itemStyle: { color, borderRadius: [3, 3, 0, 0] },
      }
    })

    const tooltipHtml = (d: Day) => {
      const row = (label: string, value: string, color?: string) =>
        `<div style="display:flex;justify-content:space-between;gap:16px">${color ? dot(color) : ''}<span style="flex:1;color:${t['ink-2']}">${label}</span><b>${value}</b></div>`
      return [
        `<div style="font-weight:600;margin-bottom:4px">${longDate(d.day)}${d.is_deadline ? ' · ⏳ prazo' : ''}</div>`,
        d.sleep_hours != null ? row('Sono', `${hoursDec(d.sleep_hours)} (${d.bedtime}→${d.wake_time})`, t['area-body']) : '',
        d.quadrant ? row('Afeto', `${QUADRANT_SHORT[d.quadrant]} (${fmt1(d.valence)})`, t[QUADRANT_TOKEN[d.quadrant]]) : '',
        d.energy != null ? row('Energia', `${fmt1(d.energy)}/5`, t['area-body']) : '',
        d.stress != null ? row('Estresse', `${fmt1(d.stress)}/5`, t['area-mind']) : '',
        d.autonomy != null ? row('Aut · Comp · Vínc', `${d.autonomy} · ${d.competence} · ${d.relatedness}`, t['area-mind']) : '',
        d.exercise_minutes ? row('Exercício', `${d.exercise_minutes} min (${d.exercise_kinds})`, t['area-body']) : '',
        d.study_minutes ? row('Estudo', `${d.study_minutes} min (${d.study_topics})`, t['area-growth']) : '',
        d.habits_tracked ? row('Hábitos', `${d.habits_done}/${d.habits_tracked}`, t['area-growth']) : '',
        d.spend_discretionary ? row('Gasto variável', money(d.spend_discretionary), t['area-money']) : '',
        d.social_with ? row('Social', d.social_with, t['area-money']) : '',
        `<div style="margin-top:4px;color:${t.muted};font-size:11px">clique para ver o dia completo</div>`,
      ].join('')
    }

    return {
      ...baseOption(t),
      animation: false,
      axisPointer: { link: [{ xAxisIndex: 'all' }], lineStyle: { color: t.axis }, label: { show: false } },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'line' },
        confine: true,
        formatter: (params: { dataIndex: number }[]) => tooltipHtml(days[params[0].dataIndex]),
      },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      dataZoom: [
        { type: 'inside', xAxisIndex: LANES.map((_, i) => i) },
        {
          type: 'slider',
          xAxisIndex: LANES.map((_, i) => i),
          bottom: 8,
          height: 22,
          left: LEFT,
          right: 16,
          borderColor: t.border,
          fillerColor: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(11,11,11,0.06)',
          handleStyle: { color: t.surface, borderColor: t.axis },
          textStyle: { color: t.muted },
          dataBackground: { lineStyle: { color: t.axis }, areaStyle: { color: t.grid } },
          labelFormatter: (_: number, v: string) => shortDate(v),
        },
      ],
      series,
    }
  }, [days, dates, t])

  const height = TOP + LANES.length * (LANE_H + GAP) + 60

  return (
    <>
      <Card
        title="Cada faixa é um trilho da sua vida"
        subtitle="Passe o mouse para ver o dia inteiro · arraste a barra de baixo ou use a roda do mouse para dar zoom · clique em um dia para abrir"
      >
        <div className="-mx-2 overflow-x-auto">
          <div className="min-w-[760px]">
            <Chart
              option={option}
              height={height}
              ariaLabel="Linha do tempo com sono, afeto, energia, estresse, necessidades, exercício, estudo, hábitos, gastos e social"
              onClick={(p) => setSelected(dates[p.dataIndex])}
            />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <Legend
            items={[
              { label: 'Agradável · energia alta', color: t['q-yellow'] },
              { label: 'Desagradável · energia alta', color: t['q-red'] },
              { label: 'Desagradável · energia baixa', color: t['q-blue'] },
              { label: 'Agradável · energia baixa', color: t['q-green'] },
            ]}
          />
          <span className="inline-flex items-center gap-2 text-xs text-ink-2">
            <span className="h-3 w-5 rounded-sm" style={{ background: t.dark ? 'rgba(255,255,255,0.08)' : 'rgba(11,11,11,0.08)' }} />
            faixa sombreada = dias de prazo apertado no trabalho
          </span>
        </div>
        <Note>
          No trilho de afeto, a barra sobe quando o dia foi agradável e desce quando foi desagradável. A cor mostra a
          energia do dia (modelo circumplexo de Russell).
        </Note>
      </Card>
      {selected && <DayDetail day={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
