import { useMemo, useState } from 'react'
import { Chart } from '../components/Chart'
import { Card, Illustration, Legend, Note, Segmented, Stat } from '../components/ui'
import { AREA_IMG, AREA_ORDER } from '../lib/areas'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, dot, FONT, type Option } from '../lib/echarts'
import { clockFromNoon, fmt0, fmt1, hoursDec, longDate, mean, money, shortDate, sum } from '../lib/format'
import { CAT, type Tokens } from '../lib/theme'
import type { AreaKey, Day } from '../types'

const STUDY_ORDER = ['SQL', 'Docker', 'Terraform', 'dbt', 'Spark', 'Kafka', 'RAG']
const FIXED = new Set(['moradia', 'contas', 'assinaturas'])
const SPEND_ORDER = ['fixos', 'alimentação', 'mercado', 'transporte', 'lazer', 'saúde', 'compras']

const weekOf = (iso: string) => {
  const d = new Date(`${iso}T12:00:00`)
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7))
  return d.toISOString().slice(0, 10)
}

function stackedWeekly(
  rows: { day: string; key: string; value: number }[],
  order: string[],
  t: Tokens,
  unit: (v: number) => string,
): Option {
  const weeks = [...new Set(rows.map((r) => weekOf(r.day)))].sort()
  const keys = order.filter((k) => rows.some((r) => r.key === k))
  const total = (w: string, k: string) => sum(rows.filter((r) => r.key === k && weekOf(r.day) === w).map((r) => r.value))
  return {
    ...baseOption(t),
    grid: { left: 52, right: 12, top: 12, bottom: 28 },
    xAxis: { type: 'category', data: weeks.map(shortDate), ...axisStyle(t), splitLine: { show: false } },
    yAxis: { type: 'value', ...axisStyle(t), axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: number) => unit(v) } },
    tooltip: {
      ...baseOption(t).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: t.grid, opacity: 0.4 } },
      formatter: (ps: { seriesName: string; value: number; color: string; name: string }[]) =>
        `<b>Semana de ${ps[0].name}</b><br/>` +
        ps.filter((p) => p.value).map((p) => `${dot(p.color)}${p.seriesName}: <b>${unit(p.value)}</b>`).join('<br/>') +
        `<br/><span style="color:${t.muted}">total ${unit(sum(ps.map((p) => p.value)))}</span>`,
    },
    series: keys.map((k) => ({
      name: k,
      type: 'bar',
      stack: 'total',
      barWidth: '55%',
      data: weeks.map((w) => total(w, k)),
      itemStyle: { color: t[CAT[order.indexOf(k)]], borderColor: t.surface, borderWidth: 1 },
    })),
  }
}

function rankedBars(items: { label: string; value: number }[], color: string, t: Tokens, unit: (v: number) => string): Option {
  const sorted = [...items].sort((a, b) => a.value - b.value)
  return {
    ...baseOption(t),
    grid: { left: 96, right: 48, top: 4, bottom: 4 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: sorted.map((i) => i.label), ...axisStyle(t), axisLine: { show: false }, splitLine: { show: false },
      axisLabel: { color: t['ink-2'], fontFamily: FONT, fontSize: 12 } },
    tooltip: { ...baseOption(t).tooltip, trigger: 'item', formatter: (p: { name: string; value: number }) => `${p.name}: <b>${unit(p.value)}</b>` },
    series: [
      {
        type: 'bar',
        data: sorted.map((i) => i.value),
        barWidth: 12,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', color: t['ink-2'], fontFamily: FONT, fontSize: 11, formatter: (p: { value: number }) => unit(p.value) },
      },
    ],
  }
}

function Body({ days }: { days: Day[] }) {
  const { t, payload, start } = useLife()
  const nights = days.filter((d) => d.bedtime_min != null && d.wake_min != null)

  const windowOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 52, right: 12, top: 12, bottom: 28 },
      xAxis: { type: 'category', data: nights.map((d) => d.day), ...axisStyle(t), splitLine: { show: false },
        axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: string) => shortDate(v) } },
      yAxis: {
        type: 'value',
        inverse: true,
        min: 600, // 22:00
        max: 1290, // 09:30
        interval: 120,
        ...axisStyle(t),
        axisLabel: { ...axisStyle(t).axisLabel, formatter: (v: number) => clockFromNoon(v) },
      },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'item',
        formatter: (p: { dataIndex: number }) => {
          const d = nights[p.dataIndex]
          return `<b>${longDate(d.day)}</b><br/>deitou ${d.bedtime} · acordou ${d.wake_time}<br/>dormiu ${hoursDec(d.sleep_hours)} · eficiência ${fmt0(d.sleep_efficiency)}%<br/>${d.sleep_onset_minutes} min para pegar no sono · ${d.awakenings} despertar(es)`
        },
      },
      series: [
        {
          type: 'custom',
          renderItem: (_: unknown, api: { value: (i: number) => number; coord: (v: number[]) => number[]; size: (v: number[]) => number[] }) => {
            const x = api.value(0)
            const top = api.coord([x, api.value(1)])
            const bottom = api.coord([x, api.value(2)])
            const w = Math.max(2, api.size([1, 0])[0] * 0.55)
            return {
              type: 'rect',
              shape: { x: top[0] - w / 2, y: top[1], width: w, height: bottom[1] - top[1], r: Math.min(3, w / 2) },
              style: { fill: t['area-body'] },
            }
          },
          encode: { x: 0, y: [1, 2] },
          data: nights.map((d, i) => [i, d.bedtime_min, d.wake_min]),
        },
      ],
    }),
    [nights, t],
  )

  const seOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 40, right: 12, top: 12, bottom: 28 },
      xAxis: { type: 'category', data: days.map((d) => shortDate(d.day)), boundaryGap: false, ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', min: 70, max: 100, interval: 10, ...axisStyle(t), axisLabel: { ...axisStyle(t).axisLabel, formatter: '{value}%' } },
      tooltip: { ...baseOption(t).tooltip, trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: t.axis } }, valueFormatter: (v: number) => `${fmt0(v)}%` },
      series: [
        {
          type: 'line',
          data: days.map((d) => d.sleep_efficiency ?? null),
          symbol: 'none',
          lineStyle: { width: 2, color: t['area-body'] },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: t.axis, type: 'solid' },
            label: { formatter: 'referência 85%', color: t['ink-2'], fontFamily: FONT, fontSize: 10, position: 'insideEndTop' },
            data: [{ yAxis: 85 }],
          },
        },
      ],
    }),
    [days, t],
  )

  const kinds = useMemo(() => {
    const m = new Map<string, number>()
    payload.events.filter((e) => e.type === 'exercise' && e.day >= start).forEach((e) => m.set(e.category ?? '—', (m.get(e.category ?? '—') ?? 0) + (e.minutes ?? 0)))
    return [...m.entries()].map(([label, value]) => ({ label, value }))
  }, [payload.events, start])

  const weeks = payload.weeks.filter((w) => w.week_start >= (days[0]?.week_start ?? start))
  return (
    <>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Sono médio" value={hoursDec(mean(days.map((d) => d.sleep_hours)))} accent={t['area-body']} />
        <Stat label="Eficiência média" value={fmt0(mean(days.map((d) => d.sleep_efficiency)))} unit="%" accent={t['area-body']}
          hint="Tempo dormindo ÷ tempo na cama. Referência usual: 85% ou mais." />
        <Stat label="Para pegar no sono" value={fmt0(mean(days.map((d) => d.sleep_onset_minutes)))} unit="min" accent={t['area-body']} />
        <Stat label="Jet lag social" value={fmt0(mean(weeks.map((w) => w.social_jetlag_minutes)))} unit="min" accent={t['area-body']}
          hint="Quanto o meio do seu sono se desloca no fim de semana em relação aos dias úteis. Quanto menor, mais regular." />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card title="Janelas de sono" subtitle="Cada barra vai da hora de deitar até a hora de acordar (diário de sono padronizado)"
          action={<Illustration name="feature-sleep" alt="" tile className="h-14 w-14" />}>
          <Chart option={windowOption} height={260} ariaLabel="Horário de dormir e acordar por noite" />
        </Card>
        <div className="min-w-0 space-y-4">
          <Card title="Eficiência do sono">
            <Chart option={seOption} height={150} ariaLabel="Eficiência do sono por dia" />
          </Card>
          <Card title="Exercício por tipo" subtitle="Minutos no período">
            <Chart option={rankedBars(kinds, t['area-body'], t, (v) => `${fmt0(v)} min`)} height={130} ariaLabel="Minutos de exercício por tipo" />
          </Card>
        </div>
      </div>
    </>
  )
}

function Mind({ days }: { days: Day[] }) {
  const { t, prevDays } = useLife()
  const stats = (rows: Day[]) => [
    mean(rows.map((d) => d.autonomy)) ?? 0,
    mean(rows.map((d) => d.competence)) ?? 0,
    mean(rows.map((d) => d.relatedness)) ?? 0,
    mean(rows.map((d) => d.energy)) ?? 0,
    6 - (mean(rows.map((d) => d.stress)) ?? 3),
  ]
  const now = stats(days)
  const prev = prevDays.length ? stats(prevDays) : null
  const option: Option = {
    ...baseOption(t),
    legend: { bottom: 0, textStyle: { color: t['ink-2'], fontFamily: FONT }, icon: 'circle', itemWidth: 10, itemHeight: 10 },
    tooltip: { ...baseOption(t).tooltip, trigger: 'item', valueFormatter: (v: number) => fmt1(v) },
    radar: {
      radius: '62%',
      center: ['50%', '46%'],
      indicator: ['Autonomia', 'Competência', 'Vínculo', 'Energia', 'Calma (6 − estresse)'].map((name) => ({ name, max: 5, min: 1 })),
      axisName: { color: t['ink-2'], fontFamily: FONT, fontSize: 12 },
      splitLine: { lineStyle: { color: t.grid } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: t.grid } },
    },
    series: [
      {
        type: 'radar',
        data: [
          ...(prev ? [{ name: 'período anterior', value: prev, lineStyle: { color: t.muted, width: 1.5 }, itemStyle: { color: t.muted }, symbol: 'none' }] : []),
          { name: 'período atual', value: now, lineStyle: { color: t['area-mind'], width: 2 }, itemStyle: { color: t['area-mind'] },
            areaStyle: { color: t['area-mind'], opacity: 0.15 }, symbolSize: 6 },
        ],
      },
    ],
  }
  const reflections = days.filter((d) => (d.journal_count ?? 0) + (d.gratitude_count ?? 0) > 0).length
  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
      <Card title="Equilíbrio da mente" subtitle="Médias de 1 a 5 · período atual vs anterior" action={<Illustration name="feature-needs" alt="" tile className="h-14 w-14" />}>
        <Chart option={option} height={340} ariaLabel="Radar de autonomia, competência, vínculo, energia e calma" />
      </Card>
      <div className="min-w-0 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Stat label="Valência média" value={fmt1(mean(days.map((d) => d.valence)))} unit="−2 a +2" accent={t['area-mind']} />
          <Stat label="Dias com reflexão" value={String(reflections)} unit={`de ${days.length}`} accent={t['area-mind']}
            hint="Dias com diário estruturado ou gratidão." />
        </div>
        <Card title="Como usar">
          <Note>
            Autonomia, competência e vínculo vêm da Teoria da Autodeterminação: quando estão satisfeitas, motivação e bem-estar
            tendem a subir no mesmo dia. Veja em “Padrões” quais delas mais se ligam ao seu humor e, em “Emoções”, o mapa
            completo do afeto.
          </Note>
        </Card>
      </div>
    </div>
  )
}

function Growth({ days }: { days: Day[] }) {
  const { t, payload, start } = useLife()
  const study = payload.study.filter((s) => s.day >= start).map((s) => ({ day: s.day, key: s.topic, value: s.minutes / 60 }))
  const books = useMemo(() => {
    const m = new Map<string, { pages: number; last: string }>()
    payload.events
      .filter((e) => e.type === 'reading' && e.label)
      .forEach((e) => m.set(e.label!, { pages: (m.get(e.label!)?.pages ?? 0) + (e.pages ?? 0), last: e.day }))
    return [...m.entries()].map(([title, v]) => ({ title, ...v })).sort((a, b) => (a.last < b.last ? 1 : -1))
  }, [payload.events])
  return (
    <>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Horas de estudo" value={fmt0(sum(days.map((d) => d.study_minutes)) / 60)} unit="h" accent={t['area-growth']} />
        <Stat label="Dias estudando" value={String(days.filter((d) => d.study_minutes).length)} unit={`de ${days.length}`} accent={t['area-growth']} />
        <Stat label="Páginas lidas" value={fmt0(sum(days.map((d) => d.reading_pages)))} accent={t['area-growth']} />
        <Stat label="Horas de trabalho / semana" value={fmt0((sum(days.map((d) => d.work_minutes)) / 60 / days.length) * 7)} unit="h" accent={t['area-growth']} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card title="Estudo por tópico" subtitle="Horas por semana, seguindo o roadmap">
          <Chart option={stackedWeekly(study, STUDY_ORDER, t, (v) => `${fmt1(v)} h`)} height={260} ariaLabel="Horas de estudo por tópico em cada semana" />
          <Legend items={STUDY_ORDER.filter((k) => study.some((s) => s.key === k)).map((k) => ({ label: k, color: t[CAT[STUDY_ORDER.indexOf(k)]] }))} />
        </Card>
        <Card title="Leituras" subtitle="Páginas registradas por livro">
          <ul className="space-y-3">
            {books.map((b) => (
              <li key={b.title}>
                <div className="flex justify-between gap-2 text-sm">
                  <span className="truncate">📖 {b.title}</span>
                  <span className="tnum shrink-0 text-ink-2">{b.pages} p.</span>
                </div>
                <div className="text-[11px] text-muted">última leitura {longDate(b.last)}</div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  )
}

function MoneySocial({ days }: { days: Day[] }) {
  const { t, payload, start } = useLife()
  const spend = payload.spending
    .filter((s) => s.day >= start)
    .map((s) => ({ day: s.day, key: FIXED.has(s.category) ? 'fixos' : s.category, value: s.amount }))
  const social = useMemo(() => {
    const m = new Map<string, number>()
    payload.events.filter((e) => e.type === 'social' && e.day >= start).forEach((e) => m.set(e.category ?? '—', (m.get(e.category ?? '—') ?? 0) + 1))
    return [...m.entries()].map(([label, value]) => ({ label, value }))
  }, [payload.events, start])
  return (
    <>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Gasto total" value={money(sum(days.map((d) => d.spend_total)))} accent={t['area-money']} />
        <Stat label="Gasto variável" value={money(sum(days.map((d) => d.spend_discretionary)))} accent={t['area-money']} hint="Sem aluguel, contas e assinaturas." />
        <Stat label="Renda" value={money(sum(days.map((d) => d.income_total)))} accent={t['area-money']} />
        <Stat label="Programas sociais" value={String(sum(days.map((d) => d.social_count)))} accent={t['area-money']} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card title="Gastos por categoria" subtitle="Por semana · aluguel, contas e assinaturas somados em “fixos”">
          <Chart option={stackedWeekly(spend, SPEND_ORDER, t, (v) => money(v))} height={260} ariaLabel="Gastos por categoria em cada semana" />
          <Legend items={SPEND_ORDER.filter((k) => spend.some((s) => s.key === k)).map((k) => ({ label: k, color: t[CAT[SPEND_ORDER.indexOf(k)]] }))} />
        </Card>
        <Card title="Com quem você passou tempo" subtitle="Número de programas no período">
          <Chart option={rankedBars(social, t['area-money'], t, (v) => `${v}`)} height={160} ariaLabel="Programas sociais por pessoa ou grupo" />
          <Note>Vínculo é uma das três necessidades psicológicas básicas. Veja em “Padrões” como os dias com programa social se relacionam com o seu humor.</Note>
        </Card>
      </div>
    </>
  )
}

export function Areas() {
  const { payload, days } = useLife()
  const [area, setArea] = useState<AreaKey>('body')
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <Segmented label="Área" value={area} onChange={setArea} options={AREA_ORDER.map((k) => ({ key: k, label: `${payload.areas[k].emoji} ${payload.areas[k].label}` }))} />
        <Illustration name={AREA_IMG[area]} alt="" className="h-10 w-10" />
      </div>
      {area === 'body' && <Body days={days} />}
      {area === 'mind' && <Mind days={days} />}
      {area === 'growth' && <Growth days={days} />}
      {area === 'money_social' && <MoneySocial days={days} />}
    </>
  )
}
