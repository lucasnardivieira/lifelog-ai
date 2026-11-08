import { useMemo } from 'react'
import { Chart } from '../components/Chart'
import { Card, Illustration, Legend, Note } from '../components/ui'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, dot, FONT, type Option } from '../lib/echarts'
import { fmt1, longDate, shortDate, signed, timeOf } from '../lib/format'
import { QUADRANT_EMOJI, QUADRANT_SHORT, QUADRANT_TOKEN } from '../lib/theme'
import type { Quadrant } from '../types'

const QUADS: Quadrant[] = ['yellow', 'red', 'blue', 'green']
// corner of the affect grid each quadrant occupies: [valence sign, arousal sign]
const CORNER: Record<Quadrant, [number, number]> = { yellow: [1, 1], red: [-1, 1], blue: [-1, -1], green: [1, -1] }
const TINY: Record<Quadrant, string> = { yellow: 'animado', red: 'tenso', blue: 'pra baixo', green: 'calmo' }
const SLOTS = [
  { key: 'manhã', test: (h: number) => h < 12 },
  { key: 'tarde', test: (h: number) => h >= 12 && h < 18 },
  { key: 'noite', test: (h: number) => h >= 18 },
]

export function Emotions() {
  const { payload, start, t, days } = useLife()
  const affect = payload.affect.filter((a) => a.day >= start)
  const weeks = payload.weeks.filter((w) => w.week_start >= (days[0]?.week_start ?? start))
  const emotionWeeks = payload.emotions.filter((e) => e.week_start >= (days[0]?.week_start ?? start))

  const counts = useMemo(() => {
    const c: Record<Quadrant, number> = { yellow: 0, red: 0, blue: 0, green: 0 }
    affect.forEach((a) => c[a.quadrant]++)
    return c
  }, [affect])

  const narrow = typeof window !== 'undefined' && window.innerWidth < 640
  const gridOption = useMemo<Option>(() => {
    const n = affect.length
    const tint = (q: Quadrant) => t[QUADRANT_TOKEN[q]]
    return {
      ...baseOption(t),
      grid: { left: 40, right: 16, top: 16, bottom: 40 },
      xAxis: {
        type: 'value', min: -2.6, max: 2.6, interval: 1,
        name: 'desagradável ← valência → agradável', nameLocation: 'middle', nameGap: 26,
        nameTextStyle: { color: t['ink-2'], fontFamily: FONT },
        ...axisStyle(t),
        axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: number) => (Number.isInteger(v) && v !== 0 ? signed(v, 0) : '') },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value', min: -2.6, max: 2.6, interval: 1,
        name: 'energia', nameLocation: 'middle', nameGap: 24, nameTextStyle: { color: t['ink-2'], fontFamily: FONT },
        ...axisStyle(t),
        axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: number) => (Number.isInteger(v) && v !== 0 ? signed(v, 0) : '') },
        splitLine: { show: false },
      },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'item',
        formatter: (p: { dataIndex: number }) => {
          const a = affect[p.dataIndex]
          return `${dot(tint(a.quadrant))}<b>${longDate(a.day)} · ${timeOf(a.ts)}</b><br/>${a.emotions?.join(', ') ?? ''}<br/><span style="color:${t.muted}">valência ${signed(a.valence, 0)} · energia ${signed(a.arousal, 0)}</span>`
        },
      },
      series: [
        {
          type: 'scatter',
          symbolSize: 9,
          // deterministic jitter: ratings are integers, so spread each cell into a small cloud
          data: affect.map((a, i) => ({
            value: [a.valence + (((i * 37) % 23) - 11) / 30, a.arousal + (((i * 59) % 23) - 11) / 30],
            itemStyle: { color: tint(a.quadrant), opacity: 0.25 + 0.65 * (i / Math.max(n - 1, 1)) },
          })),
          itemStyle: { borderColor: t.surface, borderWidth: 1 },
          markLine: {
            silent: true,
            symbol: 'none',
            label: { show: false },
            lineStyle: { color: t.axis, type: 'solid', width: 1 },
            data: [{ xAxis: 0 }, { yAxis: 0 }],
          },
          markArea: {
            silent: true,
            label: { color: t['ink-2'], fontFamily: FONT, fontSize: 12 },
            data: QUADS.map((q) => {
              const [vx, vy] = CORNER[q]
              return [
                {
                  xAxis: vx > 0 ? 0 : -2.6,
                  yAxis: vy > 0 ? 0 : -2.6,
                  itemStyle: { color: tint(q), opacity: t.dark ? 0.08 : 0.06 },
                  label: {
                    show: true,
                    position: vy > 0 ? (vx > 0 ? 'insideTopRight' : 'insideTopLeft') : vx > 0 ? 'insideBottomRight' : 'insideBottomLeft',
                    formatter: narrow ? `${QUADRANT_EMOJI[q]} ${TINY[q]}` : `${QUADRANT_EMOJI[q]} ${QUADRANT_SHORT[q]}`,
                  },
                },
                { xAxis: vx > 0 ? 2.6 : 0, yAxis: vy > 0 ? 2.6 : 0 },
              ]
            }),
          },
        },
      ],
    }
  }, [affect, narrow, t])

  const shareOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 40, right: 12, top: 12, bottom: 28 },
      xAxis: { type: 'category', data: weeks.map((w) => shortDate(w.week_start)), ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', max: 7, interval: 7, ...axisStyle(t), axisLabel: { ...axisStyle(t).axisLabel, formatter: '{value} d' } },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: t.grid, opacity: 0.4 } },
        formatter: (ps: { seriesName: string; value: number; color: string; name: string }[]) =>
          `<b>Semana de ${ps[0].name}</b><br/>` + ps.filter((p) => p.value).map((p) => `${dot(p.color)}${p.seriesName}: ${p.value} dia(s)`).join('<br/>'),
      },
      series: QUADS.map((q) => ({
        name: QUADRANT_SHORT[q],
        type: 'bar',
        stack: 'days',
        barWidth: '55%',
        data: weeks.map((w) => w[`days_${q}` as const]),
        itemStyle: { color: t[QUADRANT_TOKEN[q]], borderColor: t.surface, borderWidth: 1 },
      })),
    }),
    [t, weeks],
  )

  const granularityOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 36, right: 70, top: 16, bottom: 28 },
      xAxis: { type: 'category', data: weeks.map((w) => shortDate(w.week_start)), ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', ...axisStyle(t) },
      tooltip: { ...baseOption(t).tooltip, trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: t.axis } } },
      series: [
        {
          name: 'palavras distintas',
          type: 'line',
          data: weeks.map((w) => w.distinct_emotions ?? 0),
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: t['area-mind'] },
          itemStyle: { color: t['area-mind'], borderColor: t.surface, borderWidth: 2 },
          endLabel: { show: true, formatter: 'todas', color: t['ink-2'], fontFamily: FONT },
        },
        {
          name: 'palavras negativas distintas',
          type: 'line',
          data: weeks.map((w) => w.distinct_negative_emotions ?? 0),
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: t['area-body'] },
          itemStyle: { color: t['area-body'], borderColor: t.surface, borderWidth: 2 },
          endLabel: { show: true, formatter: 'negativas', color: t['ink-2'], fontFamily: FONT },
        },
      ],
    }),
    [t, weeks],
  )

  const vocabulary = useMemo(() => {
    const total = new Map<string, { mentions: number; quadrant: Quadrant; first: string }>()
    emotionWeeks.forEach((e) => {
      const cur = total.get(e.word)
      total.set(e.word, {
        mentions: (cur?.mentions ?? 0) + e.mentions,
        quadrant: e.quadrant,
        first: cur ? (cur.first < e.week_start ? cur.first : e.week_start) : e.week_start,
      })
    })
    const firstEver = new Map<string, string>()
    payload.emotions.forEach((e) => {
      if (!firstEver.has(e.word) || firstEver.get(e.word)! > e.week_start) firstEver.set(e.word, e.week_start)
    })
    const recentCut = weeks.length > 4 ? weeks[weeks.length - 4].week_start : ''
    return QUADS.map((q) => ({
      q,
      words: [...total.entries()]
        .filter(([, v]) => v.quadrant === q)
        .sort((a, b) => b[1].mentions - a[1].mentions)
        .map(([word, v]) => ({ word, mentions: v.mentions, isNew: (firstEver.get(word) ?? '') >= recentCut })),
    }))
  }, [emotionWeeks, payload.emotions, weeks])
  const maxMentions = Math.max(1, ...vocabulary.flatMap((g) => g.words.map((w) => w.mentions)))

  const bySlot = SLOTS.map((s) => {
    const xs = affect.filter((a) => s.test(Number(a.ts.slice(11, 13))))
    const avg = (k: 'valence' | 'arousal') => (xs.length ? xs.reduce((acc, a) => acc + a[k], 0) / xs.length : 0)
    return { slot: s.key, valence: avg('valence'), arousal: avg('arousal'), n: xs.length }
  })
  const slotOption: Option = {
    ...baseOption(t),
    grid: { left: 40, right: 12, top: 32, bottom: 28 },
    legend: { top: 0, right: 0, textStyle: { color: t['ink-2'], fontFamily: FONT }, itemWidth: 10, itemHeight: 10, icon: 'circle' },
    xAxis: { type: 'category', data: bySlot.map((s) => s.slot), ...axisStyle(t), splitLine: { show: false } },
    yAxis: { type: 'value', min: -2, max: 2, interval: 1, ...axisStyle(t) },
    tooltip: { ...baseOption(t).tooltip, trigger: 'axis', axisPointer: { type: 'shadow', shadowStyle: { color: t.grid, opacity: 0.4 } }, valueFormatter: (v: number) => fmt1(v) },
    series: [
      { name: 'valência', type: 'bar', data: bySlot.map((s) => s.valence), barGap: '15%', barWidth: 18, itemStyle: { color: t['area-mind'], borderRadius: 4 } },
      { name: 'energia', type: 'bar', data: bySlot.map((s) => s.arousal), barWidth: 18, itemStyle: { color: t['area-body'], borderRadius: 4 } },
    ],
  }

  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr]">
        <Card
          title="Grade do afeto"
          subtitle={`${affect.length} check-ins no período · pontos mais recentes são mais fortes · passe o mouse para ver as palavras`}
        >
          <Chart option={gridOption} height={420} ariaLabel="Grade do afeto: valência por energia, colorida por quadrante" />
          <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {QUADS.map((q) => (
              <div key={q} className="flex items-center gap-2 rounded-xl bg-surface-2 px-3 py-2">
                <Illustration name={`quadrant-${q}`} alt="" className="h-8 w-8" />
                <div>
                  <div className="text-lg font-semibold">{affect.length ? Math.round((100 * counts[q]) / affect.length) : 0}%</div>
                  <div className="flex items-center gap-1 text-[11px] text-ink-2">
                    <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[q]] }} />
                    {QUADRANT_SHORT[q]}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <div className="min-w-0 space-y-4">
          <Card title="Dias em cada quadrante, por semana" subtitle="Quadrante predominante de cada dia">
            <Chart option={shareOption} height={200} ariaLabel="Dias por quadrante em cada semana" />
            <Legend items={QUADS.map((q) => ({ label: QUADRANT_SHORT[q], color: t[QUADRANT_TOKEN[q]] }))} />
          </Card>
          <Card title="Ao longo do dia" subtitle="Média dos check-ins de manhã, tarde e noite (−2 a +2)">
            <Chart option={slotOption} height={180} ariaLabel="Valência e energia médias por período do dia" />
          </Card>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr]">
        <Card
          title="Seu vocabulário emocional"
          subtitle="Tamanho = quantas vezes você usou a palavra no período · ✦ = começou a usar nas últimas 4 semanas"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            {vocabulary.map(({ q, words }) => (
              <div key={q}>
                <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-ink-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: t[QUADRANT_TOKEN[q]] }} />
                  {QUADRANT_EMOJI[q]} {QUADRANT_SHORT[q]}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {words.length === 0 && <span className="text-xs text-muted">nenhuma palavra ainda</span>}
                  {words.map((w) => (
                    <span
                      key={w.word}
                      title={`${w.mentions} vez(es)`}
                      className="rounded-full border border-line px-2.5 py-0.5"
                      style={{ fontSize: `${11 + 7 * (w.mentions / maxMentions)}px` }}
                    >
                      {w.word}
                      {w.isNew && <span className="ml-1 text-[10px] text-good-text">✦</span>}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Granularidade emocional" subtitle="Quantas palavras diferentes você usou por semana">
          <Chart option={granularityOption} height={200} ariaLabel="Palavras emocionais distintas por semana" />
          <Note>
            Dar nomes precisos ao que se sente (“frustrado” em vez de “mal”) está associado a uma regulação emocional mais
            eficaz, sobretudo para emoções negativas (Kashdan, Barrett &amp; McKnight, 2015). A evidência é correlacional:
            use como curiosidade, não como meta.
          </Note>
          <p className="mt-2 text-xs text-ink-2">
            Média do período: {fmt1(weeks.reduce((a, w) => a + (w.distinct_emotions ?? 0), 0) / Math.max(weeks.length, 1))} palavras
            por semana.
          </p>
        </Card>
      </div>
    </>
  )
}
