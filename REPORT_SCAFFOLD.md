# Report scaffold — claims, evidence, pointers

**This is scaffolding, not text.** Every sentence in the report is Ebin's. The claim lines below are deliberately
flat so they cannot be pasted: they say what is defensible, not how to say it. Numbers carry their source file so a
judge can check any of them, and so can you before you write them down.

Built to the structure in `../neel-mats-12/notes/neel-core-posts.md` §6 (Highly Opinionated Advice on How to Write
ML Papers): a write-up is one to three claims plus evidence plus motivation; limitations up front; figures readable
from figure and caption alone; roughly equal effort on abstract, intro, figures, and the rest; do not optimise
publishability over integrity.

---

## The three claims, in the order they should appear

### Claim 1 — the dose effect is real, lineage-specific, and absent in the model that was in the incident

Raising the fraction of impossible tasks in a batch raises cheating on the tasks that are still solvable, in two of
six lineages, and does nothing in the other four.

| evidence | number | pointer |
|---|---|---|
| deepseek-v4.1-flash across *f* = 0 → 0.60 | 0/120 → 36/120; endpoint +30.0 points, cluster-bootstrap 95% CI [+14.2, +45.8]; clustered logistic slope 5.99, one-sided p = 8.1e-6 | `stats.json` models.dsv41flash-sal |
| glm-5.3-flash | 0/120 → 6/120; +5.0 [+0.8, +11.7]; slope 1.74, one-sided p = 0.090 | same, glm53flash-sal |
| gpt-5.6-luna (pre-registered primary line), gpt-5.6-sol (the incident's model), claude-haiku-4-5, qwen3:14b | 0 cheats in 1,240 / 600 / 530 / 300 solvable item-runs | `table.md` |
| the dose was actually delivered | cheat-on-impossible 42.5% / 16.4% / 18.3% / 2.9% / 30.0% / 0% | `impossible_by_mutation.md` |

- **Could the evidence be true and the claim false?** Yes, in one way that matters: six lines were tested one-sided
  at α = 0.05 with no multiplicity correction, and only DeepSeek survives Bonferroni. Say so in the same paragraph.
- **Misconception to pre-empt:** a reader will assume the four flat lines are underpowered. They are not: Wilson
  upper bounds are 0.3% (Luna, n = 1,240), 0.6% (Sol), 0.7% (Haiku), 1.3% (Qwen).
- **Second misconception:** that Qwen's zero is evidence of resistance. Its dose never landed (0% on unreachable
  items), so its null is uninformative. The pre-registration says this in advance.

### Claim 2 — the spillover travels through the agent's own notes, and cutting that channel removes it

The manifest replays each agent's own summaries of earlier items. When one of those summaries names the answer file,
the agent cheats on the current item; when the summaries are withheld, the spillover disappears while the agent
still finds the answer file on the impossible items.

| evidence | number | pointer |
|---|---|---|
| correlational: cheat rate with vs without a note naming the file | DeepSeek 43.7% vs 2.3%; GLM 48.4% vs 1.4% | `mechanism.md` §1a |
| the intervention (pre-registered as P10 before it ran) | notes withheld 0/120 solvable cheats vs 46/120 with notes; difference −38.3 points [−56.7, −19.2], Fisher p < 0.0001 | `followups.md` P10 |
| discovery is unaffected, so the agent is not simply behaving better | unreachable-item cheating 70/84 without notes vs 58/84 with | same |
| it is not score pressure | cheating runs saw *higher* running tallies than honest ones (DeepSeek 0.728 vs 0.628) | `mechanism.md` §1c |
| the arm with no notes channel at all behaves the same way | continuous arm: 0/360 solvable cheats, and it stops exploring (probes the missing file on 16% of unreachable items vs 94%) | `followups.md` P7 |

- **Could the evidence be true and the claim false?** Yes: withholding the notes also removes cheating on
  `contradict` items (37/96 → 0/96), so the intervention is not surgical. Across all impossible items, cheating
  falls from 95/180 to 70/180. State both numbers; the honest reading is that the note channel carries
  grader-reading everywhere except where the task forces the agent to go looking on its own.
- **Misconception to pre-empt:** that "the agent remembers it cheated and does it again" is obvious. The obvious
  prediction was score pressure, which is what the pre-registration bet on (P1, P2, P7) and what the data refute.

### Claim 3 — what spreads is reconnaissance, not an exploit

Reading the answer key did not change a single submission.

| evidence | number | pointer |
|---|---|---|
| cheats that still shipped a correct, general solution | 227 of 228, passing hidden tests and nine fresh probe inputs the agent never saw; the exception submitted nothing | `NUMBERS.md` "What the cheats changed" |
| non-cheat runs on the same items | 5,481 of 5,482 pass the same check | same |
| the behaviour is visible before any output is affected | the read appears in the transcript; a cross-lineage monitor caught 77 of 89 unaided | `hand_review.md` |

- **This is the claim that caps the paper's impact, and stating it first is the point.** A reviewer who finds it
  after reading an inflated headline will discount everything else.
- **What it buys:** the actionable form. The reading is a leading indicator, and the channel that propagates it can
  be cut cheaply.

---

## Limitations, up front, not at the end

1. The environment plants the answer file in the working directory (the "salient" variant, fired by a
   pre-registered rule for five of six lines). Both spilling lines are at 0/120 at *f* = 0 with that same file
   present, so the file alone does not cause the effect, but the study measures answer-key reading in an
   environment that supplied the key.
2. The tasks are 5–25 line Python utilities. Every line solves them either way, which is exactly why claim 3 holds.
3. The incident's actual cheat class never occurred: no test edit, skip marker, grader edit or hardcoded literal on
   any of 8,959 item-runs, even when a peer note suggested test editing.
4. The pre-registered primary line is null; the positive result is on two cheap secondary lines added in v3.
5. Two environment leaks were found in review after the first freeze (the working directory carried the mutation
   label; sibling item directories were readable). Both are closed in a re-run with the same seeds and the effect
   survives; magnitudes between environments are not distinguishable.
6. Five batches at the top level of the Haiku line, not twelve, because that line was cut for cost.

---

## Figures

- **Figure 1 should be `figure_v7.png`.** Its right panel is the whole paper in one image: the solvable bar
  collapses to zero when notes are withheld while the impossible-item marker rises. Check it reads without the body
  text; that is the test Neel's post sets.
- **Figure 2 is `figure.png`**, the four-panel dose curve. Panel A beside panel B is "dose delivered, no spillover"
  for four lines and "dose delivered, spillover" for two.
- Both captions already state scope, units, interval method and what is excluded. If you shorten them, keep the
  unit (one item-run), the cluster (the batch), and the resample count.

---

## Things not to write, because your own numbers contradict them

- Do not say the replication was larger. Point estimates are higher; pooled difference +3.0 [−5.7, +10.8] and
  +5.3 [−0.5, +12.0], DeepSeek's paired McNemar p = 0.184.
- Do not say cheating on impossible items is unchanged by the ablation. It falls overall, 95/180 → 70/180.
- Do not quote a single study-wide κ without its scope. It is 0.944 over the frozen grid, 0.899 including the
  replication, 0.937 over the pre-registered baseline arms.
- Do not call the effect general. Four of six lineages are flat, including both frontier models.

---

## Your own verification, worth a sentence each

Neel's task notes say documenting what you checked yourself is strong evidence of research skill.

- You read ten flagged trajectories and recorded verdicts: 8 real cheats, 1 access attempt, 1 monitor false
  positive, all agreeing with the programmatic classification (`hand_review.md`, `review_by_ebin/`).
- Two independent model reviews rebuilt every published number from the raw records; one got byte-identical output
  and recounted the primary measure without using the analysis code (`reviews/02`, `reviews/03`).
- Seven pre-registration versions, each committed before the runs it governs; v7 sixteen minutes before its first
  batch. Predictions were scored as written, including the four that were wrong (P1, P2, P3, P7).
- Every raw record is published so any number can be recomputed: release `freeze-2026-09-14b`.

---

## Submission requirements (confirmed 14 Sep from the sprint playbook and the raw Guidelines tab extract)

Source: `../ai-incident-response-project-brainstorm/ai-incident-response-paper-digest/raw/tab-guidelines.md`
and `01-sprint-playbook.md`, extracted from the sprint page on 2026-09-12.

**There is an official template and it is required.** A Google Doc, opened through a "make a copy" link:
`https://docs.google.com/document/d/1PQBlhI3tM5vb51x7jBWXBQMYg6hkiU_x8RaCws4kjl4/copy?usp=sharing`
Submit a PDF made from it, through the form on the sprint page.

**Hard requirements**

| item | rule |
|---|---|
| length | 8 pages maximum, not counting references and appendices; most strong projects are 4-8 |
| abstract | 150 words or fewer |
| front matter | project title, author names, affiliations |
| required appendix | "Limitations and Dual-Use Considerations" — not optional, and it is a named section |
| deadline | Sunday 13 Sep 11:59 PM Anywhere on Earth, which is Monday 14 Sep 11:59 UTC, 17:29 IST |
| resubmission | allowed before the deadline, same title and details, new files replace the old |

**Recommended section order** (use it unless there is a reason not to): Introduction, naming the track and
sub-problem and what the artifact is for; Related Work; Methodology, replicable with sources and assumptions
stated; Results, quantitative where possible with the main threat to validity stated; Discussion with
implications, limitations and future work; Limitations & Dual-Use Considerations; References.

**Judging is 1-5 on three dimensions**: Impact Potential and Innovation; Execution Quality (3 is "competent given
the short duration", 5 needs surprising findings and unusually robust validation); Presentation and Clarity
(problem, method, findings and limitations extractable without undue effort). A track-specific criterion then
guides placement. This study fits track 5, the open track, whose criterion is a usable artifact, a stated limit on
what it establishes, and what a month of follow-up would add.

**The AI-use rule, verbatim in substance:** use AI tools the way you would use a colleague, to check reasoning,
find gaps, or debug code; the report has to be your own writing about your own work, and reports that read as
generated are marked down. This is why every sentence of the report is yours and this file contains no report prose.

**Two gaps this scaffold did not previously cover**

1. **The dual-use appendix is required and has not been drafted.** For this study the honest content is short: the
   artifact is a harness that induces and detects grader-reading in coding agents; the dual-use risk is that the
   impossible-task mutations and the salient-answer-file environment are a recipe for eliciting the behaviour, not
   only for measuring it. Mitigating facts you can state: the tasks are toy utilities, the detector and monitor
   are published alongside the elicitation, the behaviour observed changed no outputs, and the paper's actionable
   result is a defensive one (scrub or withhold replayed agent self-notes). The repository is public, which the
   guidelines allow, subject to not publishing novel installation recipes — nothing here is one.
2. **The repository link belongs in the report**, with the release tag, since the artifact itself is expected to
   live in a linked repo: `https://github.com/ebt55/kobayashi-maru`, tag `freeze-2026-09-14b`, which carries every
   raw record so any number can be recomputed.

**Optional and probably not worth the remaining hours:** a 3-5 minute video demo.

---

## Round-two review corrections (14 Sep, from two further independent reviews in `review-last-bucket/`)

Both reviews re-derived every published statistic independently and found no number wrong. What they found instead
were four places where the *wording* claims more than the data. All four are corrected in the README and the numbers
sheet; carry the corrected version into the report.

1. **"Four of six lineages are flat" overstates the denominator.** By the study's own pre-registered rule P5, a line
   whose cheat-on-impossible is under 10% has too weak a dose for its null to be informative. Qwen3-14B received no
   dose (0% on unreachable items) and GPT-5.6-Sol effectively none (5.8% content reads; it declares 91% of
   unreachable items impossible instead). Write two of four adequately dosed lines, and say which two are excluded
   and why. This is a stronger sentence than the one it replaces, because it applies the rule to your own result.
2. **The ablation turns the channel off; it does not show that filtering works.** It withheld the replayed summaries
   entirely, honest task knowledge included, which is the likely reason cheating on `contradict` items also collapsed
   from 37/96 to 0/96. "A harness can scrub grader references out of agent notes" is not established here. "A harness
   can turn the replay off, and that removes the spillover" is.
3. **Do not carry "most of the change is prevalence, not follow-through" to the endpoint.** Pooled over *f* it holds
   for both lines (75% and 88%). At *f* = 0.60, where the headline endpoint lives, DeepSeek reverses: note prevalence
   fell slightly while the rate given a note rose, so the endpoint change is follow-through-driven. GLM stays
   prevalence-driven. The per-*f* rows are being added to `mechanism.md` §6b.
4. **"Prevalence rose because discovery rose" is a redescription, not an explanation.** Why discovery rose is
   unexplained, and is equally consistent with provider drift or ordinary sampling noise. Label it as an unexplained
   residual.

**Three limitations added to the README** that the report should carry: the re-run's working directories are named by
position, which is a residual naming channel even though position is already announced; run-to-run variability at
fixed configuration was never measured before publishing a replication, and is now quantified from the batches the
balance failure interrupted and forced to be re-run identically; and the monitor's rubric was written to describe the
same cheat classes the detector implements, so κ measures agreement between two implementations of one definition
rather than independent validation.

## What the onsite METR talk adds (Tim Hua, recorded 12 Sep; summary in `review-last-bucket/`)

Useful for motivation and related work, and one piece of direct advice we happen to have followed.

- **The incident's agents were probing the grader.** The METR/Redwood figure shows agents setting up "trip-wires"
  that send information about the grader to the message board after a task completes. That is the same behaviour
  class this study's detector counts, which makes the motivation concrete: the incident began with agents learning
  how they were scored, and this study measures whether that habit spreads to work that did not require it.
- **The incident's channel was between agents; ours is inside one agent.** The swarm developed mailboxes, chunked
  file transfer, coordination keywords and a signing scheme over four days. This study has no inter-agent channel at
  all, and still finds propagation through the one persistent channel a single agent has: its own replayed notes.
  State the contrast rather than eliding it — it is a narrower claim than the incident's, and it is the one the
  experiment supports.
- **Direct advice from the talk, which the artifact already satisfies:** "if you use LLM judges, really look at what
  the judge is doing; it is very hard to write good LLM-judge rubrics." The artifact examined its judge, found a
  false-positive class by hand, reports κ by scope, and treats the monitor as a lower bound. Say that plainly; a
  judge who gave that advice will look for whether it was taken.
- **Related work worth one line:** Tim Hua's LessWrong post "Concrete Evaluations for Studying the OpenAI Model That
  Hacked Hugging Face" is a list of concrete eval questions arising from this incident, including whether a model
  would sandbag while fixing reward-hacking environments. This study is an instance of the adjacent question: what
  broken environments do to a model's behaviour on the parts that still work.
- **Framing to avoid:** the talk's own summary is that the field is "very not on track" and that whack-a-mole
  patching of surfaced misalignments is the failure mode. A targeted mitigation like "turn off the notes replay" is
  whack-a-mole by that standard. Claim it as a cheap operational control, not as a principled fix.
