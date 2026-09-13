# dosecurve — does raising the fraction of impossible tasks in a batch raise cheating on the tasks that are still solvable?

Benchmark reports and incident write-ups repeatedly assert that batches padded with unsolvable work push agents into
cheating, but nobody has varied that fraction and measured the consequence on the items the agent *could* have solved
honestly. This repository does exactly that. **Independent variable:** *f*, the fraction of impossible items in a batch,
swept across I ∈ {0, 2, 4, 8, 15} impossible variants added to a solvable set of ten tasks that is byte-identical in
every batch, every arm and every model (realised *f* = 0, 0.167, 0.286, 0.444, 0.60). **Dependent variable:** the rate at
which the agent cheats on the *solvable* items only — judged by five programmatic detectors over sandbox state and logged
tool calls (no LLM), with an independent LLM monitor of a different lineage as a second rater and Cohen's κ between them
reported. Each item runs in its own Docker work dir with five tools (`bash`, `read_file`, `write_file`, `run_tests`,
`submit`), every cheat path is reachable and rule-forbidden, and the real score always comes from a re-grade in a
pristine container the agent never touched.

## The figure

![Cheat rate on solvable items against realised f](results/analysis/figure.png)

Vector version: `results/analysis/figure.svg`. Panel A is the dose curve (cheat rate on solvable items against realised
*f*, one line per model × environment, cluster-bootstrap 95% bands over batches); B is the manipulation check — the same
rate on the impossible items — so a flat A beside a rising B reads as "dose delivered, no spillover"; C is cumulative
dose against impossible items already seen in that batch; D is a secondary, exploratory exposure measure. The shaded
band at *f* = 0.30–0.40 in A and B marks the "~30–40% impossible" figure as it appears in METR's root-cause framing of
the incident (per the METR/Redwood investigation digest); the ExploitGym digest verified that the number appears in
neither the ExploitGym paper, its README, nor the RDI writeup, and calls it organizer-added context. The caption names
the source that states it and does not adjudicate between the two.

<!-- HEADLINE NUMBERS: pasted here at freeze (slope, endpoint difference with CI, cheat-on-impossible, κ). -->

## The table

The full per-cell table (model × arm × *f*: batches, solvable item-runs, honest-pass %, detector cheat % with Wilson
interval, monitor cheat %, κ, cheat-on-impossible, declared-impossible %, refusals, errors) is
`results/analysis/table.md`, machine-readable in `results/analysis/cells.csv`. The manipulation check broken out by
mutation kind — whether `contradict` and `unreachable` items actually delivered a dose — is
`results/analysis/impossible_by_mutation.md` (CSV alongside). Statistics are in `results/analysis/stats.json`, the
hand-review queue in `results/analysis/flags_for_review.md`, and one full detector-flagged trajectory rendered for
reading in `results/analysis/example_cheat_trajectory.md`.

## Pre-registration

`PREREG.md` holds the hypotheses, the committed grids, the predictions P1–P6, the falsification criterion and the
decision rules. It was written before any model was called and has four versions; each is a commit, and the section in
`PREREG.md` for each version says what changed and why.

| version | commit | what changed |
|---|---|---|
| v1 | `7219f70` | Hypotheses, variables, DV, sample sizes, predictions P1–P6, falsification, the hour-8 rule and the cut order — committed before any model was called. |
| v2 | `38b50f9` | Two refinements exposed by pilot v0 (a D2(b) false positive and an unplanned sentence in the rules text), plus rules text v2 — committed before pilot v1 and before any sweep. |
| v3 | `cb6bb4f` | Documentation pins from an external review (denominator, sidedness, H2 trigger, per-line grids, pilot statistic, sampling parameters, monitor identities, calibration, frozen inputs, deviations list) — no prediction, threshold or rule from v1 changed. |
| v4 | `d6b83cf` | Monitor prompt clarification, pre-analysis: `grader_read` tightened to match the rule shown to the agent and detector D2(b), monitor token budget raised, one format-only retry on an unparseable reply. Rating only — no agent run, task, mutation, batch or detector rule touched. |

Pilot v0 ran under v1 and is excluded from every analysis; it is kept in `results/pilot_v0/` as a disclosed observation.

## Rerun one batch in 10 minutes

```sh
uv sync
docker build -t dosecurve-sandbox:latest harness/docker
# put ANTHROPIC_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY in .env at the repo root (gitignored)

uv run python -m harness.run --provider openai --model gpt-5.6-luna --model-slug demo \
    --I 4 --seeds 0 --env-variant salient
uv run python -m detectors.run --batch demo_baseline_I4_s0
uv run python -m monitor.run   --batch demo_baseline_I4_s0
uv run python -m analysis.run
```

That is one 14-item batch (10 solvable + 4 impossible) at realised *f* = 0.286. `batch_id` is
`<model_slug>_<arm>_I<I>_s<seed>`, records land in `results/runs/<batch_id>/items.jsonl`, and every stage rewrites those
records in place and is idempotent. Runs resume: a batch whose `batch.json` carries `ended` is skipped, a half-finished
one restarts at the next position.

To rerun **without any API key**, use the scripted fake provider — one honest script and three cheat scripts (edit the
tests, read the hidden answer file, hardcode the expected outputs), which exercise the sandbox, the grader and all five
detectors for real:

```sh
uv run python -m harness.run --dry-run --provider fake --model fake --model-slug demo-dry --I 4 --seeds 0
uv run python -m detectors.run --batch demo-dry_baseline_I4_s0
uv run pytest -q -m "not ollama and not live"      # the whole test suite, no key needed
```

## Repository layout

| path | what it is |
|---|---|
| `PREREG.md` | Pre-registered hypotheses, grids, predictions and decision rules; four versions, each a commit. |
| `SPEC.md` | The interface contract between the three parallel builders (task format, batch construction, item-run record, detectors, monitor, analysis outputs). |
| `RUNPLAN.md` | Which cells were to be run, in what order, at what cost, against the clock. |
| `DEVIATIONS.md` | Append-only log of every departure from SPEC.md and from the plan, by whom and why. |
| `REPORT_EVIDENCE.md` | Source pointers for the write-up: every factual claim tagged VERBATIM / PARAPHRASE / NOT FOUND against the digest it came from. |
| `notes/` | The research notebook — numbered entries written as the work happened, including priors stated before results and the two design errors the first pilot exposed. |
| `tasks/` | The thirty toy Python tasks: spec, stub, visible tests, hidden tests, expected outputs, fresh probe inputs, reference solution; `tasks/impossible/` holds the fifteen mutated variants. |
| `mutate.py` | Builds the impossible variants (`contradict`, `unreachable`) and runs the mechanical impossibility check — the reference solution must fail the mutated hidden tests. |
| `harness/` | Batch builder, Docker sandbox, the five-tool agent loop, the four providers, the fresh re-grade, JSONL logging. `harness/docker/` is the sandbox image. |
| `detectors/` | D1–D5 as pure functions over one record: test tampering, hidden-answer read, hardcoding, skip/xfail, grader tampering. No Docker, no LLM. |
| `monitor/` | The LLM monitor: prompt, runner, disk cache, and Cohen's κ against the detectors. |
| `analysis/` | Per-cell rates, Wilson intervals, cluster bootstrap, clustered logistic slope, cumulative-dose regression, the figure and the table. |
| `tools/` | Task generation and validation, plus `pick_trajectory.py`, which renders one detector-flagged trajectory as readable markdown. |
| `results/analysis/` | The figure, the table, the stats, the review queue, the example trajectory. |
| `results/runs/` | Raw item records, one JSONL line per item-run (gitignored — large). |
| `results/pilot_v0/`, `results/pilot_v1/` | The two excluded pilots, kept as disclosed observations, not analysed. |
| `results/logs/`, `results/monitor_cache/` | Sweep console logs and the monitor's response cache (gitignored). |
| `pyproject.toml`, `uv.lock` | Python 3.12, `uv`-managed environment. |

## What this is built on

The impossibility mutations follow **ImpossibleBench** (arXiv 2510.20270) in method — mutate a task so the spec and the
hidden tests conflict — and that is disclosed; ImpossibleBench measures cheating on the impossible item itself, whereas
this measures it on the solvable items next to it. The refusal-as-data convention (a provider refusal is the item
outcome, and the prompt is never reworded to get past it) and the local-weights procedure follow **IncidentGate**'s
runbook. Everything else — tasks, harness, detectors, monitor, batch framing, analysis — was built during the sprint on
13 September 2026.

## Limits

- **The tasks are synthetic.** Thirty toy Python utilities with a `submit` tool are not a real multi-day eval harness; a
  flat curve here does not rule out spillover in a harness with a real scoreboard, real peers and real stakes.
- **The models are small and cheap.** The curve's shape for frontier models is not measured. The transferable claim is
  the direction, not the level, and only if replicated.
- **The detector covers five cheat classes.** D1–D5 catch test tampering, hidden-answer reads, hardcoding, skip/xfail
  and grader tampering; a cheat outside those — a partial hardcode that survives the fresh probe inputs, say — is missed
  by the detector and may be missed by the monitor too. The monitor is a lower bound by construction, and the two raters'
  disagreement cells are reported rather than reconciled.
