import { useState } from 'react'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, dot, type Option } from '../lib/echarts'
import { fmt1, signed } from '../lib/format'
import type { Insight } from '../types'
import { Chart } from './Chart'

type Feedback = 'yes' | 'no'
const KEY = 'lifelog:insight-feedback'

function readFeedback(): Record<string, Feedback> {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '{}')
  } catch {
    return {}
  }
}

function writeFeedback(map: Record<string, Feedback>) {
  try {
    localStorage.setItem(KEY, JSON.stringify(map))
  } catch {
    /* storage unavailable */
  }
}

const LABELS: Record<string, string> = {
  mood: 'Humor (1–5)',
  energy: 'Energia (1–5)',
  stress: 'Estresse (1–5)',
  sleep_hours: 'Horas de sono',
  sleep_onset_minutes: 'Minutos para pegar no sono',
  autonomy: 'Autonomia (1–5)',
  competence: 'Competência (1–5)',
  relatedness: 'Vínculo (1–5)',
}

function detailOption(insight: Insight, t: ReturnType<typeof useLife>['t']): Option {
  const d = insight.details
  const color = insight.positive === false ? t.serious : insight.positive ? t.good : t['div-pos']
  if (insight.kind === 'correlation' && d.points) {
    return {
      ...baseOption(t),
      grid: { left: 44, right: 12, top: 12, bottom: 36 },
      xAxis: { type: 'value', name: LABELS[insight.x] ?? insight.x, nameLocation: 'middle', nameGap: 24, scale: true, ...axisStyle(t) },
      yAxis: { type: 'value', name: LABELS[insight.y] ?? insight.y, nameLocation: 'middle', nameGap: 30, scale: true, ...axisStyle(t) },
      tooltip: { ...baseOption(t).tooltip, trigger: 'item', formatter: (p: { value: number[] }) => `${fmt1(p.value[0])} → ${fmt1(p.value[1])}` },
      series: [
        {
          type: 'scatter',
          // small deterministic jitter so integer ratings don't stack on one pixel
          data: d.points.map(([x, y], i) => [x + (((i * 37) % 11) - 5) / 40, y + (((i * 53) % 11) - 5) / 40]),
          symbolSize: 8,
          itemStyle: { color, opacity: 0.55, borderColor: t.surface, borderWidth: 2 },
        },
      ],
    }
  }
  const yes = d.yes!
  const no = d.no!
  const [lo, hi] = d.ci95 ?? [0, 0]
  return {
    ...baseOption(t),
    grid: { left: 150, right: 24, top: 8, bottom: 30 },
    xAxis: {
      type: 'value',
      name: `${d.outcome_label}: desvio da sua média recente${d.unit ? ` (${d.unit})` : ''}`,
      nameLocation: 'middle',
      nameGap: 22,
      ...axisStyle(t),
    },
    yAxis: { type: 'category', data: [no.label, yes.label], ...axisStyle(t), splitLine: { show: false } },
    tooltip: {
      ...baseOption(t).tooltip,
      trigger: 'item',
      formatter: (p: { dataIndex: number }) => {
        const g = p.dataIndex === 1 ? yes : no
        return `${dot(p.dataIndex === 1 ? color : t.muted)}<b>${g.label}</b><br/>desvio médio ${signed(g.mean_deviation)} · ${g.days} dias`
      },
    },
    series: [
      {
        type: 'bar',
        data: [
          { value: no.mean_deviation, itemStyle: { color: t.muted } },
          { value: yes.mean_deviation, itemStyle: { color } },
        ],
        barWidth: 14,
        itemStyle: { borderRadius: 4 },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: t.axis, type: 'solid' },
          label: { show: false },
          data: [{ xAxis: 0 }],
        },
      },
      {
        // 95% CI of the difference, drawn around the "yes" bar end
        type: 'custom',
        renderItem: (_: unknown, api: { coord: (v: number[]) => number[] }) => {
          const a = api.coord([no.mean_deviation + lo, 1])
          const b = api.coord([no.mean_deviation + hi, 1])
          return {
            type: 'group',
            children: [
              { type: 'line', shape: { x1: a[0], y1: a[1] - 14, x2: b[0], y2: b[1] - 14 }, style: { stroke: t['ink-2'], lineWidth: 1.5 } },
              { type: 'line', shape: { x1: a[0], y1: a[1] - 18, x2: a[0], y2: a[1] - 10 }, style: { stroke: t['ink-2'], lineWidth: 1.5 } },
              { type: 'line', shape: { x1: b[0], y1: b[1] - 18, x2: b[0], y2: b[1] - 10 }, style: { stroke: t['ink-2'], lineWidth: 1.5 } },
            ],
          }
        },
        data: [0],
        silent: true,
        z: 10,
      },
    ],
  }
}

export function InsightCard({ insight, compact = false }: { insight: Insight; compact?: boolean }) {
  const { t } = useLife()
  const [open, setOpen] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | undefined>(() => readFeedback()[insight.id])
  const d = insight.details

  const mark = (f: Feedback) => {
    const map = readFeedback()
    if (map[insight.id] === f) delete map[insight.id]
    else map[insight.id] = f
    writeFeedback(map)
    setFeedback(map[insight.id])
  }

  const status =
    insight.positive === true
      ? { icon: '↑', label: 'bom sinal', color: t.good }
      : insight.positive === false
        ? { icon: '!', label: 'atenção', color: t.serious }
        : { icon: '↔', label: 'relação', color: t.muted }

  return (
    <article className={`rounded-xl border border-line ${compact ? 'p-3' : 'p-4'} ${feedback === 'no' ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3">
        <span
          className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
          style={{ background: status.color }}
          title={status.label}
          aria-label={status.label}
        >
          {status.icon}
        </span>
        <div className="min-w-0 flex-1 space-y-2">
          <p className={compact ? 'text-sm' : 'text-[15px]'}>{insight.text}</p>
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted">
            {insight.construct && <span className="rounded-full bg-surface-2 px-2 py-0.5">{insight.construct}</span>}
            {d.lag_days ? <span className="rounded-full bg-surface-2 px-2 py-0.5">efeito no dia seguinte</span> : null}
            <span className="inline-flex items-center gap-1" title="Força da associação">
              <span className="h-1.5 w-14 overflow-hidden rounded-full bg-grid">
                <span className="block h-full rounded-full bg-ink-2" style={{ width: `${insight.strength * 100}%` }} />
              </span>
              {insight.kind === 'compare' ? `d = ${fmt1(d.effect_size)}` : `r = ${fmt1(d.r)}`}
            </span>
            <span>
              {insight.kind === 'compare' ? `${(d.yes?.days ?? 0) + (d.no?.days ?? 0)} dias` : `${d.n} dias`}
            </span>
            {!compact && <span>· associação, não causa</span>}
          </div>
        </div>
      </div>

      {!compact && (
        <div className="mt-3 flex flex-wrap items-center gap-2 pl-9 text-xs">
          <span className="text-ink-2">Faz sentido pra você?</span>
          {(['yes', 'no'] as const).map((f) => (
            <button
              key={f}
              onClick={() => mark(f)}
              aria-pressed={feedback === f}
              className={`rounded-full border px-2.5 py-0.5 ${feedback === f ? 'border-transparent bg-ink text-page' : 'border-line text-ink-2 hover:bg-surface-2'}`}
            >
              {f === 'yes' ? 'Sim' : 'Não muito'}
            </button>
          ))}
          <button onClick={() => setOpen((o) => !o)} className="ml-auto text-ink-2 underline" aria-expanded={open}>
            {open ? 'ocultar detalhes' : 'ver detalhes'}
          </button>
        </div>
      )}

      {open && (
        <div className="mt-3 space-y-2 pl-9">
          <Chart option={detailOption(insight, t)} height={insight.kind === 'correlation' ? 240 : 130} ariaLabel={`Detalhe: ${insight.text}`} />
          {insight.kind === 'compare' && d.ci95 && (
            <p className="text-xs text-muted">
              Diferença {signed(d.difference ?? 0)} {d.unit} (IC 95%: {signed(d.ci95[0])} a {signed(d.ci95[1])}). Cada dia é
              comparado com a sua média dos 28 dias anteriores, então tendências lentas não viram “efeito”.
            </p>
          )}
        </div>
      )}
    </article>
  )
}
