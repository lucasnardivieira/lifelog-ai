import { useMemo } from 'react'
import { Chart } from '../components/Chart'
import { SupportCard } from '../components/Support'
import { Card, Illustration, Note, Stat } from '../components/ui'
import { useLife } from '../lib/context'
import { axisStyle, baseOption, FONT, type Option } from '../lib/echarts'
import { fmt0, fmt1, longDate, mean, shortDate } from '../lib/format'

export function Wellbeing() {
  const { payload, start, t, days } = useLife()
  const inst = payload.instruments
  const rows = payload.assessments.filter((a) => a.day >= start)
  const who5 = rows.filter((a) => a.instrument === 'who5')
  const pss = rows.filter((a) => a.instrument === 'pss10')
  const ls = rows.filter((a) => a.instrument === 'life_satisfaction')
  const lastWho5 = who5[who5.length - 1]
  const prevWho5 = who5[who5.length - 2]
  const lowWeeks = who5.filter((w) => w.low_wellbeing_flag).length
  const who5Delta = lastWho5 && prevWho5 ? lastWho5.score - prevWho5.score : null

  const who5Option = useMemo<Option>(() => {
    const ref = inst.who5.reference ?? 52
    return {
      ...baseOption(t),
      grid: { left: 40, right: 16, top: 20, bottom: 28 },
      xAxis: { type: 'category', data: who5.map((w) => shortDate(w.day)), boundaryGap: false, ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', min: 0, max: 100, interval: 25, ...axisStyle(t) },
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: 'axis',
        axisPointer: { type: 'line', lineStyle: { color: t.axis } },
        formatter: (p: { dataIndex: number }[]) => {
          const w = who5[p[0].dataIndex]
          return `<b>${longDate(w.day)}</b><br/>WHO-5: <b>${w.score}</b>/100${w.low_wellbeing_flag ? `<br/><span style="color:${t.serious}">▲ abaixo da referência</span>` : ''}`
        },
      },
      series: [
        {
          type: 'line',
          data: who5.map((w) => ({
            value: w.score,
            symbol: w.low_wellbeing_flag ? 'triangle' : 'circle',
            symbolSize: w.low_wellbeing_flag ? 11 : 7,
            itemStyle: w.low_wellbeing_flag ? { color: t.serious, borderColor: t.surface, borderWidth: 2 } : undefined,
          })),
          lineStyle: { width: 2, color: t['area-mind'] },
          itemStyle: { color: t['area-mind'], borderColor: t.surface, borderWidth: 2 },
          markArea: {
            silent: true,
            itemStyle: { color: t.serious, opacity: t.dark ? 0.1 : 0.08 },
            label: { show: true, position: 'insideBottomRight', color: t['ink-2'], fontFamily: FONT, fontSize: 11, formatter: inst.who5.reference_label },
            data: [[{ yAxis: 0 }, { yAxis: ref }]],
          },
        },
      ],
    }
  }, [inst, t, who5])

  const pssOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 36, right: 12, top: 16, bottom: 28 },
      xAxis: { type: 'category', data: pss.map((p) => shortDate(p.day)), ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', min: 0, max: 40, interval: 10, ...axisStyle(t) },
      tooltip: { ...baseOption(t).tooltip, trigger: 'axis', axisPointer: { type: 'shadow', shadowStyle: { color: t.grid, opacity: 0.4 } }, valueFormatter: (v: number) => `${v}/40` },
      series: [{ type: 'bar', data: pss.map((p) => p.score), barWidth: 22, itemStyle: { color: t['area-mind'], borderRadius: [4, 4, 0, 0] } }],
    }),
    [pss, t],
  )

  const lsOption = useMemo<Option>(
    () => ({
      ...baseOption(t),
      grid: { left: 30, right: 12, top: 16, bottom: 28 },
      xAxis: { type: 'category', data: ls.map((p) => shortDate(p.day)), ...axisStyle(t), splitLine: { show: false } },
      yAxis: { type: 'value', min: 0, max: 10, interval: 5, ...axisStyle(t) },
      tooltip: { ...baseOption(t).tooltip, trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: t.axis } }, valueFormatter: (v: number) => `${v}/10` },
      series: [
        {
          type: 'line',
          data: ls.map((p) => p.score),
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { width: 2, color: t['area-growth'] },
          itemStyle: { color: t['area-growth'], borderColor: t.surface, borderWidth: 2 },
        },
      ],
    }),
    [ls, t],
  )

  const needs = {
    autonomy: mean(days.map((d) => d.autonomy)),
    competence: mean(days.map((d) => d.competence)),
    relatedness: mean(days.map((d) => d.relatedness)),
  }

  return (
    <>
      {payload.support.highlight && <SupportCard />}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          label="WHO-5 mais recente"
          value={lastWho5 ? fmt0(lastWho5.score) : '—'}
          unit="/100"
          accent={t['area-mind']}
          delta={who5Delta != null ? (who5Delta === 0 ? '≈ igual à semana anterior' : `${who5Delta > 0 ? '+' : '−'}${Math.abs(who5Delta)} vs semana anterior`) : undefined}
          deltaGood={who5Delta ? who5Delta > 0 : undefined}
        />
        <Stat label="Média WHO-5 no período" value={fmt0(mean(who5.map((w) => w.score)))} unit="/100" accent={t['area-mind']} />
        <Stat
          label="Semanas abaixo da referência"
          value={String(lowWeeks)}
          unit={`de ${who5.length}`}
          accent={t.serious}
          hint="WHO-5 abaixo de 52 (bruto < 13): um sinal para conversar com alguém, não um diagnóstico."
        />
        <Stat label="Satisfação com a vida" value={ls.length ? fmt0(ls[ls.length - 1].score) : '—'} unit="/10" accent={t['area-growth']} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card title={inst.who5.name} subtitle="Respondido aos domingos · 5 perguntas sobre as últimas 2 semanas">
          <Chart option={who5Option} height={260} ariaLabel="Evolução semanal do WHO-5 com faixa de referência" />
          <Note>
            Fonte: {inst.who5.source}. Triângulos = semanas abaixo da referência. O WHO-5 mede bem-estar; ele não diagnostica
            depressão.
          </Note>
        </Card>
        <Card title="Como ler" action={<Illustration name="feature-wellbeing" alt="" tile className="h-16 w-16" />}>
          <ul className="space-y-3 text-sm text-ink-2">
            <li>
              <b className="text-ink">WHO-5 (semanal):</b> de 0 a 100. Ficar abaixo de 52 por algumas semanas seguidas é um bom
              motivo para conversar com alguém de confiança ou com um profissional.
            </li>
            <li>
              <b className="text-ink">PSS-10 (mensal):</b> estresse percebido no último mês, de 0 a 40. Quanto maior, mais estresse.
            </li>
            <li>
              <b className="text-ink">Satisfação com a vida (mensal):</b> uma nota geral de 0 a 10, que costuma mudar devagar.
            </li>
          </ul>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card title={inst.pss10.name} subtitle="Último dia de cada mês">
          <Chart option={pssOption} height={180} ariaLabel="PSS-10 mensal" />
          <Note>Fonte: {inst.pss10.source}.</Note>
        </Card>
        <Card title={inst.life_satisfaction.name} subtitle="Último dia de cada mês">
          <Chart option={lsOption} height={180} ariaLabel="Satisfação com a vida mensal" />
          <Note>Fonte: {inst.life_satisfaction.source}.</Note>
        </Card>
        <Card
          title="Necessidades psicológicas básicas"
          subtitle="Média diária no período (1–5)"
          action={<Illustration name="feature-needs" alt="" tile className="h-14 w-14" />}
        >
          <ul className="space-y-3">
            {(
              [
                ['autonomy', 'Autonomia', 'fazer as coisas por escolha própria'],
                ['competence', 'Competência', 'sentir-se capaz e eficaz'],
                ['relatedness', 'Vínculo', 'sentir-se próximo(a) das pessoas'],
              ] as const
            ).map(([k, label, hint]) => (
              <li key={k}>
                <div className="flex justify-between gap-2 text-sm">
                  <span>
                    <b>{label}</b> <span className="text-xs text-muted">— {hint}</span>
                  </span>
                  <span className="tnum font-semibold">{fmt1(needs[k])}</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-grid">
                  <div className="h-full rounded-full" style={{ width: `${((needs[k] ?? 0) / 5) * 100}%`, background: t['area-mind'] }} />
                </div>
              </li>
            ))}
          </ul>
          <Note>Teoria da Autodeterminação (Ryan &amp; Deci). Itens adaptados para uso diário: não é uma escala validada nesse formato.</Note>
        </Card>
      </div>

      {!payload.support.highlight && <SupportCard compact />}
    </>
  )
}
