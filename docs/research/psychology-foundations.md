# Psychology foundations for lifelog-ai

Research note, 2026-11-08. It records which psychological constructs the life log measures, why, how
each is scored, and how it shows up in the product. The goal is **self-understanding grounded in
validated constructs**. Diagnosis is out of scope (see [§9 Safety & ethics](#9-safety--ethics)).

## TL;DR: what changes in the product

| Construct (framework) | Identifier we log | Cadence | Where it shows up |
|---|---|---|---|
| Core affect: Russell's circumplex | `valence` (−2…+2), `arousal` (−2…+2), quadrant | daily, any time | affect grid, quadrant strip on the timeline |
| Emotional granularity: Barrett, Kashdan | emotion words from a PT-BR vocabulary | with each affect check-in | emotion vocabulary, weekly granularity index |
| Sleep: Consensus Sleep Diary (Carney 2012) | bedtime, sleep-onset latency, awakenings, wake time, quality, rested | every morning | sleep window chart, efficiency, regularity |
| Basic psychological needs: SDT (Ryan & Deci) | autonomy, competence, relatedness (1–5) | end of day | needs triangle, needs → mood patterns |
| Well-being: WHO-5 (validated in BR-PT) | 5 items, 0–5 each → 0–100 | weekly (Sunday) | well-being trend with reference band |
| Perceived stress: PSS-10 (validated in BR-PT) | 10 items, 0–4 each | monthly | stress trend |
| Life satisfaction: single 0–10 item | `life_satisfaction` | monthly | life-satisfaction trend |
| Pleasure & mastery: behavioral activation | `pleasure`, `mastery` (0–10) on activities | optional, per activity | "what gives you energy" ranking, next-day effect |
| Habits & intentions: Lally, Gollwitzer, Harkin | if-then plans, habit check-ins | daily | habit-strength curves instead of fragile streaks |
| Reflection: Emmons & McCullough, Pennebaker | gratitude (≈ weekly), structured journaling prompts | weekly / free | diary, prompts |
| Personal analytics: within-person methods | person-mean deviations, lag-1 effects, detrending | computed | "Padrões" and n-of-1 "Experimentos" |

---

## 1. Measurement approach: daily diary with light EMA

- A **once-daily diary** keeps most of the protection against recall bias that full experience
  sampling (EMA) offers, at far lower burden. A common design pairs a few momentary check-ins with
  an evening diary ([Simply Psychology, EMA](https://www.simplypsychology.org/ecological-momentary-assessment.html)).
- **Single items are fine for daily tracking but are not scales.** Momentary single items capture
  real day-to-day variability, but their convergent validity with retrospective scales is only
  modest ([Rohde et al., 2026](https://onlinelibrary.wiley.com/doi/10.1002/brb3.71598)). Brief
  multi-item momentary measures can keep reliability while improving compliance
  ([Univ. of Bristol](https://research-information.bris.ac.uk/en/publications/ecological-momentary-assessment-of-mood-reliability-and-validity-/)).
  → **Design:** short daily items for patterns, plus **validated multi-item instruments on a slower
  cadence** (WHO-5 weekly, PSS-10 monthly) as anchors.
- **Electronic, time-stamped entries** prevent the back-filling problem of paper diaries
  ([PMC3773004](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3773004/)). Every event already
  carries `occurred_at`. We also store `logged_at` so late entries can be flagged.
- **Kahneman's Day Reconstruction Method** reproduces experience-sampling results with less burden
  ([Kahneman et al., 2004](https://greatergood.berkeley.edu/images/uploads/Kahneman-DayReconstructionMethod.pdf);
  [Princeton](https://kahneman.scholar.princeton.edu/document/6)). It is a candidate for an optional
  weekly "reconstruct yesterday" flow (future).

## 2. Core affect: Russell's circumplex

Affect is modeled on two axes, **valence** (unpleasant ↔ pleasant) and **arousal** (low ↔ high
energy). Any emotion is a combination of the two ([Russell, 1980](https://www.researchgate.net/figure/Circumplex-Model-of-Affect-Russell-1980_fig2_221391863)).
Mood apps such as MoodMap use exactly these axes, and a chatbot study used the circumplex as its
gold-standard mood self-report, with words and icons per quadrant
([arXiv 1907.10664](https://arxiv.org/pdf/1907.10664);
[Quantified Self](https://quantifiedself.com/blog/measuring-mood-current-resea/)). Known limitation:
co-occurring and mixed emotions are flattened ([affective recommender survey](https://arxiv.org/pdf/2508.20289)).
That is why we add emotion words (§3).

**Identifiers**
- `valence` ∈ {−2,−1,0,+1,+2} and `arousal` ∈ {−2,−1,0,+1,+2}, picked on a 5×5 affect grid.
- Derived quadrant, using the familiar four-color convention:
  🟡 pleasant + high energy (excited, motivated) · 🔴 unpleasant + high energy (anxious, irritated) ·
  🔵 unpleasant + low energy (sad, tired) · 🟢 pleasant + low energy (calm, content).
- The legacy `mood` 1–5 maps to `valence + 3` so old data keeps working.

**Product:** an affect grid scatter (each check-in is a dot, colored by recency), a quadrant strip
on the timeline, and "time in each quadrant" per week.

## 3. Emotional granularity

People who **differentiate negative emotions finely** ("frustrated" vs "disappointed" vs
"anxious") show modestly better mental health and more effective emotion regulation. The evidence
is consistent but mostly correlational, and it is stronger for negative than for positive emotions
([Kashdan, Barrett & McKnight, 2015](https://www.affective-science.org/pubs/2015/kashdan-et-all-unpacking-emotion-differentiation-2015.pdf);
[editorial, Front. Psychol.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9714615/);
[UvA meta-analysis](https://pure.uva.nl/ws/files/34194610/_15_4_2019_Emotion_di.pdf)).
Putting feelings into words (**affect labeling**) is linked to lower emotional intensity in lab
studies (Lieberman et al., 2007; summarized in
[Myndgard](https://myndgard.com/posts/2026-05-20-why-naming-feelings-helps/)).

**Identifiers:** `emotions: list[str]` from a curated PT-BR vocabulary of about 40 words, each
placed in a quadrant. Claude can suggest words from free text, and the user confirms.
**Derived:** a weekly *granularity index*, counting distinct emotion words used, reported
separately for negative and positive emotions.
**Product:** the "Vocabulário emocional" view, which shows words used this month and nudges the
user toward more precise words when the same generic word repeats ("mal" → "frustrado? cansado?
preocupado?").

## 4. Sleep: Consensus Sleep Diary

The Consensus Sleep Diary standardizes prospective sleep self-monitoring. Its core metrics are
total sleep time, sleep-onset latency (SOL), wake after sleep onset (WASO), and sleep efficiency
(SE = time asleep ÷ time in bed × 100)
([Carney et al., 2012](https://www.researchgate.net/publication/221796012_The_Consensus_Sleep_Diary_Standardizing_Prospective_Sleep_Self-Monitoring);
[psychometrics in insomnia](https://www.researchgate.net/publication/303593292_Psychometric_Properties_of_the_Consensus_Sleep_Diary_in_Those_With_Insomnia_Disorder)).

**Identifiers (morning entry):** `bedtime`, `sol_minutes`, `awakenings`, `waso_minutes`,
`wake_time`, `out_of_bed`, `quality` (1–5, very poor → very good), `rested` (1–5).
**Derived in dbt:** TST, TIB, SE %, sleep midpoint, and **regularity**, the variability of the
midpoint across days, including the weekday-vs-weekend gap ("social jetlag").
**Product:** a sleep window chart (horizontal bars from bedtime to wake time per night), SE and
regularity tiles, and sleep → next-day patterns.

## 5. Basic psychological needs: Self-Determination Theory

SDT names three innate needs: **autonomy, competence, relatedness**. When they are satisfied they
support motivation and well-being, and when they are frustrated they are linked to ill-being
([Ryan & Deci, 2000](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf);
[Vansteenkiste & Ryan, 2013](https://selfdeterminationtheory.org/wp-content/uploads/2014/07/2013_VansteenkisteRyan_JOPI2.pdf)).
Diary studies show that **day-to-day fluctuations** in need satisfaction track same-day mood and
vitality, and each need contributes independently (Sheldon, Reis & Ryan, 1996; review in
[PMC8558380](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8558380/)).

**Identifiers (end of day, 1–5):**
- *Autonomia:* "Hoje senti que fiz as coisas por escolha própria."
- *Competência:* "Hoje me senti capaz e eficaz no que fiz."
- *Vínculo:* "Hoje me senti próximo(a) de pessoas importantes para mim."

These are adapted for daily use from BPNSFS-style diary items. They are **not** a validated scale
in this form, and the UI says so.
**Product:** a needs triangle per week, plus patterns such as "on days with low autonomy, your
valence is lower" (within-person, §8).

## 6. Validated anchor instruments (slower cadence)

| Instrument | Items / scoring | Brazilian validation | Use |
|---|---|---|---|
| **WHO-5 Well-Being Index** | 5 items, 0–5 → raw 0–25, ×4 = 0–100. Raw < 13 (< 50%) is the commonly used flag for low well-being and a reason to seek evaluation ([PMC9517039](https://pmc.ncbi.nlm.nih.gov/articles/PMC9517039/)) | α = 0.83, single factor, rural adults ([de Souza & Hidalgo, 2012](https://pubmed.ncbi.nlm.nih.gov/21912931/)). The best Brazilian cutoff is not confirmed in our sources. | Weekly, Sunday |
| **PSS-10 Perceived Stress** | 10 items, 0–4 (4 reverse-scored) → 0–40 | Reliable in Brazil, α 0.87 total ([Reis et al.](https://www.researchgate.net/publication/40907483_Perceived_Stress_Scale_Reliability_and_Validity_Study_in_Brazil); [Luft et al., elderly](https://www.scielo.br/j/rsp/a/bgpXDHZXQXNqVS8JLnLdLhr/?format=html&lang=pt)). The PSS-4 one-factor fit is borderline in Brazil ([SciELO CFA](http://www.scielo.br/j/prc/a/9WxhmCvsBVZdqTLdwbjq6Ly/?lang=pt)), so we use the PSS-10. | Monthly |
| **Life satisfaction (0–10 single item)** | "No geral, quão satisfeito(a) você está com sua vida hoje?" | A plain life-satisfaction item outperforms the Cantril ladder in recent large studies ([Global Flourishing comparison](https://link.springer.com/article/10.1007/s11482-026-10623-5); [adolescents](https://link.springer.com/article/10.1007/s12187-026-10338-x)) | Monthly |
| *(optional)* **PERMA-Profiler** | 23 items, 0–10; 5 PERMA domains + health, negative emotion, loneliness ([Butler & Kern](https://www.researchgate.net/publication/310512308_The_PERMA-Profiler_A_brief_multidimensional_measure_of_flourishing); [Penn PPC](https://ppc.sas.upenn.edu/resources/questionnaires-researchers/perma-profiler)) | Psychometrics were found insufficient in one Australian sample ([PMC6927648](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6927648/)), so it is used only as a reflection lens | Quarterly, optional |

**Licensing:** WHO-5 is free to use. PSS is free for non-commercial use. The PERMA-Profiler is free
for non-commercial use with citation. Item wording comes from the published Brazilian versions,
with the source cited in-app.

## 7. Behavior: activation, habits, intentions, reflection

- **Behavioral activation:** rating activities for **pleasure and mastery** is a core BA
  technique. Achieved and expected mastery and pleasure track improvement in depression
  ([J. Affect. Disord., 2018](https://www.sciencedirect.com/science/article/abs/pii/S0165032718300338)).
  In an EMA study, **yesterday's enjoyment of activities predicted today's mood, while activity
  frequency did not** ([PMC10738807](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10738807/)).
  → Optional `pleasure`/`mastery` (0–10) on exercise, social, study and leisure events, plus the
  insight "the activities that give you the most energy".
- **Habit formation:** the median time to automaticity was about 66 days, with a very wide spread
  (18–254), and **missing a single day did not materially hurt** habit formation
  ([Lally interview, Univ. of Surrey](https://www.surrey.ac.uk/news/does-it-really-take-66-days-form-habit-we-asked-expert-dr-pippa-lally)).
  → A **habit-strength curve** (exponentially weighted repetition) instead of all-or-nothing
  streaks, so one missed day does not reset to zero. A "~66 days (range is wide)" marker is shown
  as context, not as a deadline.
- **Implementation intentions:** if-then plans ("Se forem 22h, então desligo as telas") had a
  medium-to-large effect on goal attainment, d = 0.65 across 94 tests
  ([Gollwitzer & Sheeran, 2006](https://kops.uni-konstanz.de/handle/123456789/10973)).
  → Each habit/goal stores an `if_then` plan, shown next to its curve.
- **Self-monitoring:** monitoring goal progress promotes attainment (d+ = 0.40), more so when
  progress is **physically recorded** and reported
  ([Harkin et al., 2016](https://eprints.whiterose.ac.uk/id/eprint/87431/)).
  → The weekly report is the "reporting" moment, and the dashboard makes progress visible.
- **Gratitude & expressive writing:** gratitude journaling improved well-being and optimism versus
  control writing (Emmons & McCullough, 2003). Meta-analyses mostly find gains, with smaller
  effects than the popular press claims, and it is **unclear whether daily beats weekly**
  ([Templeton white paper](https://www.templeton.org/wp-content/uploads/2018/05/Gratitude_whitepaper_fnl.pdf)).
  Expressive writing about emotional experiences is associated with better well-being (Pennebaker;
  Frattaroli, 2006).
  → Gratitude prompts about weekly rather than daily, to avoid habituation. Journaling prompts are
  **structured and time-bounded** (what happened → what I felt → what I can do), not open-ended
  rumination ([rumination RCT](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11350318/)).

## 8. Personal analytics done right (n-of-1)

- **Within-person, not between-person.** Self-tracking asks "on *my* worse-sleep days, is *my*
  mood lower?", so compare each day to **your own average** (person-mean deviations)
  ([Wang & Maxwell](https://www.researchgate.net/publication/274262743_On_Disaggregating_Between-Person_and_Within-Person_Effects_With_Longitudinal_Data_Using_Multilevel_Models)).
- **Detrend first.** Person-mean centering fails when a variable trends over time (for example,
  sleep slowly improving), because the trend gets mistaken for an effect
  ([Curran & Bauer, 2011](https://curran.web.unc.edu/wp-content/uploads/sites/6785/2015/03/CurranBauer2011.pdf)).
  → Remove a rolling 28-day baseline before comparing.
- **Lag-1 effects** (yesterday's X → today's Y) are more plausible as influences than same-day
  correlations. Individual lag profiles differ, which is exactly why n-of-1 makes sense
  ([DTVEM-RE preprint](https://arxiv.org/pdf/2606.14116)).
- **Report uncertainty and sample size.** Require enough days (≥ 10 per group), show effect sizes
  and confidence intervals (bootstrap), and label findings **"associação, não causa"**.
- **Self-experiments.** Turn a suspicion into an A/B test ("2 weeks no screens after 22h vs 2
  weeks as usual"), then compare with the same statistics. This is the honest way to get closer
  to causality on one person.

## 9. Safety & ethics

- **Not a diagnostic tool.** Mental-health apps that label users ("this app said I had severe
  depression") can cause harm ([CHI 2024](https://dl.acm.org/doi/full/10.1145/3613904.3642178)).
  WHO-5 scores are shown as *well-being*, never as "depression". A low score triggers a gentle
  suggestion to talk to a professional.
- **Crisis resources that fit the user's country.** Only about 35% of mental-health apps show crisis
  resources, and some point to the wrong country's numbers
  ([crisis-readiness study](https://escholarship.org/content/qt43c2t9zt/qt43c2t9zt_noSplash_c259875c0510d77d2e2954599cd87932.pdf)).
  → A persistent "Precisa conversar?" link: **CVV 188** (free, 24h) and chat at cvv.org.br
  ([CONASS](https://www.conass.org.br/prevencao-ao-suicidio-conta-com-ligacao-gratuita-em-todo-pais/)),
  plus SAMU 192 for emergencies. It is shown proactively when WHO-5 raw < 13 or after several
  days in the unpleasant/low-energy quadrant.
- **The user's interpretation comes first.** Data-driven readings shouldn't override how a
  person understands their own experience
  ([epistemic injustice analysis](https://link.springer.com/article/10.1007/s10676-024-09765-7)).
  Insights are phrased as questions ("Faz sentido pra você?"), and the user can dismiss or annotate them.
- **No engagement traps.** Avoid dependency-driven design such as aggressive streaks and guilt
  notifications ([Front. Psychiatry, 2025](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1581779/full)).
  Habit curves forgive missed days.
- **Privacy.** Mental-health data is sensitive personal data under the LGPD. Real data stays local
  (`data/private/`, gitignored), the public demo is synthetic, and there are no third-party analytics.

## 10. Open questions

- The best Brazilian WHO-5 cutoff: confirm in the full text of de Souza & Hidalgo (2012).
- Exact PT-BR item wording for WHO-5 and PSS-10: take it from the validated Brazilian versions.
- PERMA-Profiler PT-BR availability and licensing for an optional quarterly check.
