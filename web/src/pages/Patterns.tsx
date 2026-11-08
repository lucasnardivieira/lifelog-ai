import { useMemo, useState } from 'react'
import { InsightCard } from '../components/InsightCard'
import { Card, Chip, Illustration } from '../components/ui'
import { useLife } from '../lib/context'

type Tone = 'all' | 'good' | 'attention' | 'link'

export function Patterns() {
  const { payload } = useLife()
  const [construct, setConstruct] = useState<string>('todos')
  const [tone, setTone] = useState<Tone>('all')
  const [nextDayOnly, setNextDayOnly] = useState(false)
  const [showAll, setShowAll] = useState(false)

  const constructs = useMemo(
    () => ['todos', ...new Set(payload.insights.map((i) => i.construct).filter(Boolean))],
    [payload.insights],
  )

  const shown = payload.insights.filter(
    (i) =>
      (construct === 'todos' || i.construct === construct) &&
      (tone === 'all' ||
        (tone === 'good' && i.positive === true) ||
        (tone === 'attention' && i.positive === false) ||
        (tone === 'link' && i.positive === null)) &&
      (!nextDayOnly || (i.details.lag_days ?? 0) > 0),
  )

  // one suggestion per condition, from next-day effects that look like good news
  const experiments = payload.insights
    .filter((i) => (i.details.lag_days ?? 0) > 0 && i.positive)
    .filter((i, idx, all) => all.findIndex((j) => j.x === i.x) === idx)
    .slice(0, 2)

  return (
    <>
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row">
          <Illustration name="feature-patterns" alt="" tile className="h-24 w-24 shrink-0" />
          <div className="space-y-2 text-sm text-ink-2">
            <p>
              <b className="text-ink">Você comparado com você mesmo.</b> Cada dia é comparado com a sua própria média dos 28
              dias anteriores, então tendências lentas (como dormir cada vez melhor) não viram “efeito”.
            </p>
            <p>
              <b className="text-ink">Ontem → hoje.</b> Alguns padrões olham o dia seguinte (por exemplo, noite sem telas → sono
              da noite). Isso é mais plausível como influência do que coisas que acontecem juntas no mesmo dia.
            </p>
            <p>
              <b className="text-ink">Só o que é consistente.</b> Aparecem apenas diferenças com pelo menos 10 dias de cada lado e
              intervalo de confiança de 95% que não cruza o zero. Mesmo assim, é <b>associação, não causa</b>, e você é quem
              melhor interpreta a própria vida.
            </p>
          </div>
        </div>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        {constructs.map((c) => (
          <Chip key={c} active={construct === c} onClick={() => setConstruct(c)}>
            {c}
          </Chip>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {(
          [
            ['all', 'Todos'],
            ['good', '↑ Bons sinais'],
            ['attention', '! Pontos de atenção'],
            ['link', '↔ Relações'],
          ] as const
        ).map(([k, label]) => (
          <Chip key={k} active={tone === k} onClick={() => setTone(k)}>
            {label}
          </Chip>
        ))}
        <Chip active={nextDayOnly} onClick={() => setNextDayOnly((v) => !v)}>
          só efeitos no dia seguinte
        </Chip>
        <span className="ml-auto text-xs text-muted">{shown.length} padrões · calculados com todo o histórico</span>
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        {(showAll ? shown : shown.slice(0, 12)).map((i) => (
          <InsightCard key={i.id} insight={i} />
        ))}
      </div>
      {!showAll && shown.length > 12 && (
        <div className="text-center">
          <button onClick={() => setShowAll(true)} className="rounded-full border border-line px-4 py-2 text-sm hover:bg-surface-2">
            Mostrar todos os {shown.length} padrões
          </button>
        </div>
      )}

      {experiments.length > 0 && (
        <Card title="Quer testar de verdade?" subtitle="Um experimento pessoal chega mais perto de causa do que observar">
          <ul className="space-y-3 text-sm">
            {experiments.map((i) => (
              <li key={i.id} className="rounded-xl bg-surface-2 p-3">
                <b>Hipótese:</b> {i.text}
                <br />
                <span className="text-ink-2">
                  <b>Teste:</b> alterne 2 semanas fazendo “{i.details.yes?.label}” e 2 semanas no seu normal, mantendo o resto parecido.
                  Depois compare “{i.details.outcome_label}” entre os blocos aqui mesmo.
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  )
}
