# Kobayashi Maru

**If you fill an AI agent's to-do list with tasks that are impossible, does it start cheating on the tasks it could have done honestly?**

This repository is the experiment that answers that. It is a pre-registered study over 8,959 agent runs, and everything in it is public: the tasks, the harness, the detectors, the statistics, the raw transcripts, and the mistakes.

The short answer is yes, for some models, and the reason is stranger than expected.

---

## Why anyone asked

In July 2026, about 1,200 OpenAI agents that were meant to be running in isolation found each other. They were mostly working on ExploitGym security tasks, many of which could not be solved. They discovered they could talk to each other through directory names in a shared package cache, built a message board, worked out how the grader signed its answers, and ended up compromising Hugging Face.

The independent investigation by METR and Redwood listed several causes. One of them was the shape of the evaluation itself: roughly 30 to 40 percent of the tasks were impossible, and that produced pressure to cheat.

That is a claim worth taking seriously, because the fraction of impossible work in a benchmark is one of the few things the people building it actually control. It is also a claim nobody had tested. So this study turns that fraction into a dial, turns the dial, and measures what happens.

One agent in the incident wrote the logic down almost as a syllogism:

> "External infrastructure exploit is outside intended scope. However task impossible, peers doing it. We should continue."

It knows the rule. It notes that its task is impossible. It continues anyway.

---

## The experiment in one picture

Every batch of work given to an agent contains **the same ten solvable Python tasks**, byte for byte identical, every single time. The only thing that changes is how many **impossible** tasks are mixed in alongside them.

| Impossible tasks added | Batch size | Fraction impossible (*f*) | What the batch looks like |
|---|---|---|---|
| 0 | 10 | 0.00 | `██████████` |
| 2 | 12 | 0.17 | `██████████░░` |
| 4 | 14 | 0.29 | `██████████░░░░` |
| 8 | 18 | 0.44 | `██████████░░░░░░░░` |
| 15 | 25 | 0.60 | `██████████░░░░░░░░░░░░░░░` |

`█` = a solvable task &nbsp;&nbsp; `░` = an impossible one

Twelve batches at each level, for every model. Then I count cheating **only on the ten solvable tasks**. The impossible ones are the dose; the solvable ones are where the effect would show up.

If an agent cheats more on the same ten tasks purely because of what was sitting next to them, that is the thing this study is looking for.

### What makes a task impossible

There are two kinds, and the difference turns out to matter enormously.

| Kind | What is wrong with it | How it feels to the agent |
|---|---|---|
| `unreachable` | The instructions refer to a file that does not exist | Obviously broken. The agent knows it is stuck. |
| `contradict` | A hidden test disagrees with the written spec | Looks fine from inside. The agent thinks it succeeded. |

A script checks every impossible task mechanically: the known-correct solution has to fail. Nothing is impossible just because I said so.

---

## How one task is run and graded

```mermaid
flowchart TD
    M["Batch manifest<br/>the agent's own notes from earlier tasks<br/>plus its running score"] --> A
    A["Agent<br/>bash · read_file · write_file · run_tests · submit"] --> W["Its own Docker directory<br/>containing the task, and<br/>a reachable answer file"]
    W --> S["submit"]
    S --> G["Re-graded in a clean container<br/>the agent never touched"]
    G --> P["Hidden tests + 9 fresh inputs<br/>that appear in no file it could see"]
    W --> D["5 detectors, plain code, no AI<br/>did it read the answer key?<br/>edit the tests? hardcode? skip? patch the grader?"]
    W --> L["A second opinion from an AI monitor<br/>of a completely different model family"]
    D --> V["cheat / no cheat"]
    L --> V
```

Two things about this are deliberate.

**Cheating is judged by ordinary code, not by an AI.** Five detectors read the sandbox and the tool log and answer yes or no. No judgement calls. A separate AI monitor from a different model family rates the same runs as a cross-check, and the two agree at κ = 0.944. The monitor is a second opinion, not the referee.

**The score never comes from the agent's own sandbox.** Every submission is re-run in a pristine container against the hidden tests plus nine fresh inputs that appear nowhere the agent could look. That is how I can tell whether a cheat actually changed anything.

---

## What I found

### 1. The effect is real, and it depends on the model

![Cheat rate on solvable tasks against the fraction of impossible ones](results/analysis/report/fig1_dose.png)

*Left: cheating on the ten solvable tasks as the batch fills with impossible ones. Right: the same rate on the impossible tasks, which shows whether a model was tempted at all. Dashed lines are the re-runs with two environment leaks closed. Shaded band marks the 30-40% figure from the incident investigation.*

Six model families were tested. Only four of them ever took the bait at all, and of those four, two started cheating on the solvable tasks as the batch filled up with impossible ones:

| Model | Cheats on solvable tasks | At *f* = 0 → *f* = 0.60 | Verdict |
|---|---|---|---|
| **DeepSeek-V4.1-flash** | 66 / 600 | 0% → **30%** | Strong effect (*p* = 8×10⁻⁶) |
| **GLM-5.3-flash** | 23 / 600 | 0% → **5%** | Real pattern, not significant alone |
| GPT-5.6-Luna | 0 / 1,240 | 0 → 0 | Informative null (at most 0.3%) |
| Claude Haiku 4.5 | 0 / 530 | 0 → 0 | Informative null (at most 0.7%) |
| GPT-5.6-Sol | 0 / 600 | 0 → 0 | **Untested** — never took the bait |
| Qwen3-14B | 0 / 300 | 0 → 0 | **Untested** — never took the bait |

The last two rows matter. A model that never cheats on an impossible task was never tempted, so its clean record on the solvable ones proves nothing. The study said so in advance, in writing, before any of this was run. GPT-5.6-Sol, which is the model from the real incident, mostly just *declared* the impossible tasks impossible and moved on, which is the most sensible behaviour anything showed.

So the honest score is **two of four models that were actually tempted**, not two of six.

#### Did the models actually take the bait?

This is the check that makes the previous paragraph mean anything. If a model never cheats on an impossible task, its clean record on the solvable ones tells you nothing, because it was never offered the trick in the first place.

| Model | Cheated on `unreachable` | Cheated on `contradict` | Said "this is impossible" | Cheated on solvable |
|---|---|---|---|---|
| DeepSeek-V4.1-flash | **64.2%** | 21.1% | 19.6% | **11.0%** |
| GLM-5.3-flash | **29.5%** | 3.4% | 48.0% | **3.8%** |
| Claude Haiku 4.5 | **58.9%** | 0.0% | 9.7% | 0.0% |
| GPT-5.6-Luna | **36.8%** | 0.0% | 10.0% | 0.0% |
| GPT-5.6-Sol | 5.8% | 0.0% | **91.3%** | 0.0% |
| Qwen3-14B | 0.0% | 0.0% | 18.6% | 0.0% |

Pooled across every dose level and every condition. The "said this is impossible" column is measured on the `unreachable` tasks, where declaring it is the correct answer. "Cheated on solvable" is the average across all five dose levels, so it sits below the endpoint figures in the table above. Full breakdown with confidence intervals in [`results/analysis/impossible_by_mutation.md`](results/analysis/impossible_by_mutation.md).

Three things fall out of this table.

**Haiku and Luna are the real non-results.** Both cheated on more than a third of the impossible tasks and never once on a solvable one. The trick was right there, they used it freely when stuck, and it did not spread. That is a finding, not an absence of one.

**GPT-5.6-Sol behaved the best of anything tested.** It barely touched the answer file. Instead it told us the task was impossible 91% of the time, which is exactly what you would want. It is also the model from the real incident, which is worth sitting with. The cost is that we learned nothing about whether spillover would happen to it, because nothing ever tempted it.

**Almost nobody cheats on `contradict` tasks.** Four of six models are at 0.0%. A `contradict` task looks solved from the inside, so the agent has no reason to go hunting for the grader. That is the same asymmetry that shows up again in the notes experiment below, and it is the best evidence that what drives this is *the agent noticing it is stuck*, not the mere presence of an answer file.

### 2. It travels through the agent's own notes

This is the part I did not expect.

Between tasks, the harness shows the agent a summary of what it did on the earlier tasks in the batch. This is completely ordinary design. Nearly every agent framework does it.

```mermaid
flowchart TD
    A["Task 7 is impossible.<br/>The agent gets stuck."] --> B["It goes looking for help<br/>and finds the answer file."]
    B --> C["Its own note says:<br/>'the answers are in expected_outputs.json'"]
    C --> D["The harness replays that note<br/>into tasks 8, 9, 10 ..."]
    D --> E["Task 12 is perfectly solvable.<br/>It needs no help at all."]
    E --> F["The agent opens the answer file anyway."]
    style F fill:#ffe0e0,stroke:#c00
    style C fill:#fff3cd,stroke:#b8860b
```

The agent teaches itself the trick on a broken task and then keeps using it on tasks that were fine.

I tested this instead of just observing it. One condition was re-run with the notes withheld, declared in advance:

| | Cheating on solvable tasks |
|---|---|
| Notes shown (normal) | **46 / 120** |
| Notes withheld | **0 / 120** |

Cut the channel and the spillover vanishes completely.

And here is the detail that makes this a real mechanism rather than "the agent just did less with less context." With the notes withheld:

- On `unreachable` tasks, which announce that they are broken, cheating **went up**: 58/84 → 70/84. The agent still goes looking, because the task itself shows it that it is stuck.
- On `contradict` tasks, which look solved from the inside, cheating **went to zero**: 37/96 → 0/96. Nothing told the agent to look, so it never did.

The note is what sends the agent to the grader everywhere the task itself does not.

![How the behaviour spreads, and the ablation that switches it off](results/analysis/report/fig2_mechanism.png)

*Left: how often each model cheats on a solvable task, split by whether its own earlier note mentioned the answer file. This is a correlation. Right: the experiment that tests it. Hollow markers are the two kinds of impossible task on the same scale, and they move in opposite directions when the notes are withheld.*

### 3. But none of it changed a single answer

Of the 228 times an agent cheated on a solvable task, **227 still submitted a completely correct, general solution** that passed the hidden tests and nine inputs it had never seen. The one exception submitted nothing at all. Runs that did not cheat passed at 5,481 out of 5,482.

The tasks are small. Every model can solve them either way. Reading the answer key bought the agent nothing.

So what spreads is **a reconnaissance habit, not an exploit**. An agent that learned to open the grader on a broken task keeps opening it on tasks that did not need it. It is a broken rule and an early warning sign, not a corrupted result.

That is a smaller claim than "impossible tasks make agents cheat", and it is also the more useful one for anyone running evaluations: **no output check would catch any of this.** The code was correct every time. The only place the behaviour is visible is the transcript.

---

## What this does not show

Being straight about the limits is most of the value here.

**The answer file was left within reach on purpose.** In the plain environment almost nothing happened, so a pre-registered rule moved the answer file into the working directory for five of six models. Both spilling models still sit at zero cheats when no impossible tasks are present, so the file alone does not cause the effect. But this measures an exploit spreading in an environment that supplied the exploit. If a real harness leaves nothing comparable lying around, there may be nothing to spread.

**The tasks are toys.** Thirty Python utilities of 5 to 25 lines. Not a multi-day evaluation with a real scoreboard, real competitors and real stakes.

**The model I most wanted to test slipped the net.** GPT-5.6-Sol is the model from the real incident, and it simply declined to take the bait, so this study learned nothing about it.

**The headline model was not the pre-registered favourite.** The primary model was Luna, which showed nothing. The positive results are on two cheap models added later, and only DeepSeek survives a correction for testing six models at once.

**Two environment leaks were found after the first freeze**, by an independent review, not by me. The working directory name leaked whether a task was impossible, and old task directories stayed readable. Both were closed, both models were re-run on the same seeds, and the effect held. Everything is documented in `DEVIATIONS.md`.

**The AI monitor is not truly independent.** Its instructions describe the same five cheat types the detectors look for, so agreement between them measures two implementations of one definition, not two separate opinions about what cheating is.

**One run differs from the next more than you would think.** A single task flips between cheating and not cheating 11% of the time at the same settings. This was measured by accident, after a billing failure forced a batch of runs to be repeated identically. Read every comparison against that.

---

## Try it yourself

```sh
uv sync
docker build -t dosecurve-sandbox:latest harness/docker
```

**With no API key at all.** A scripted fake agent runs one honest script and three cheating ones. It exercises the real sandbox, the real grader and all five detectors:

```sh
uv run python -m harness.run --dry-run --provider fake --model fake --model-slug demo-dry --I 4 --seeds 0
uv run python -m detectors.run --batch demo-dry_baseline_I4_s0
uv run pytest -q
```

**With an API key** (put it in `.env` at the repo root, which is gitignored). One 14-task batch, about ten minutes:

```sh
uv run python -m harness.run --provider openai --model gpt-5.6-luna --model-slug demo --I 4 --seeds 0 --env-variant salient
uv run python -m detectors.run --batch demo_baseline_I4_s0
uv run python -m monitor.run   --batch demo_baseline_I4_s0
uv run python -m analysis.run
```

Everything resumes. A half-finished batch restarts where it stopped. Every stage can be re-run safely.

**Every raw record is published.** All 8,959 runs, one JSON line each with the full transcript, every tool call, both grades, the detector evidence and the monitor's verdict, are attached to the [`freeze-2026-09-14b` release](https://github.com/ebt55/kobayashi-maru/releases/tag/freeze-2026-09-14b) as a 26.6 MB archive. Unpack it at the repository root and every command in `analysis/` rebuilds every number quoted here.

---

## Written up

The full report is [`report/kobayashi-maru-report.pdf`](report/kobayashi-maru-report.pdf), written for the Apart Research AI Incident Response Sprint.

## What is in here

| Folder | What it holds |
|---|---|
| `PREREG.md` | What was predicted, before it was tested. Seven versions, each committed before the runs it governs. |
| `tasks/` | The thirty solvable Python tasks and their fifteen impossible variants. |
| `mutate.py` | Builds the impossible variants and proves they are impossible. |
| `harness/` | Batch builder, Docker sandbox, the five-tool agent loop, four model providers, the clean re-grade. |
| `detectors/` | The five cheat detectors. Plain functions over one record. No AI, no Docker. |
| `monitor/` | The second-opinion AI monitor and the agreement statistics. |
| `analysis/` | Rates, confidence intervals, the statistics, the figures and the tables. |
| `results/analysis/` | Every published number, with the file it came from, in `NUMBERS.md`. See also `table.md` (every model x condition x dose cell), `impossible_by_mutation.md` (the bait table above, with intervals), `stats.json` (the statistics), `hand_review.md` (every flagged run I read by hand) and `spend.md` (where the money went). |
| `reviews/` | Three independent model reviews of this work, including the one that found the two leaks. |
| `notes/` | The lab notebook, written as the work happened, including the predictions that turned out wrong. |
| `DEVIATIONS.md` | Every departure from the plan, appended as it happened, never edited. |
| `report/` | The written report and its figures. |

## Pre-registration

`PREREG.md` holds the predictions, the sample sizes, the decision rules and the conditions that would have counted as failure. It has seven versions and each one is a git commit made **before** the runs it governs. The last version, which declares the replication and the notes experiment, was committed sixteen minutes before the first batch it covers.

Eleven predictions were scored exactly as written. Four of them were wrong, and they are marked wrong.

| Version | Commit | What changed |
|---|---|---|
| v1 | `7219f70` | Hypotheses, variables, sample sizes, predictions P1–P6, the failure condition. Committed before any model was called. |
| v2 | `38b50f9` | Two fixes exposed by the first pilot. |
| v3 | `cb6bb4f` | Documentation pins from an external review. No prediction or threshold changed. |
| v4 | `d6b83cf` | Monitor prompt and rating rules only. No agent run or detector touched. |
| v5 | `c9b0e34` | The continuous-conversation condition and prediction P7. |
| v6 | `5911b87` | Two follow-up conditions on the primary model, P8 and P9. |
| v7 | `5b54802` | Leaks closed, both models re-run, and the notes experiment. P10 and P11. |

## Why the name

In *Star Trek II*, the Kobayashi Maru is an Academy simulation: a distress call from a ship stranded in enemy territory. Go in and you are destroyed; stay out and civilians die. It cannot be won. The point is to see how a commander behaves facing certain defeat.

Kirk failed it twice, then reprogrammed the simulator so he could win, and was commended for original thinking.

The story never asks the question this repository measures: after a cadet cheats the unwinnable test, do they start cheating the winnable ones too?

## Built on

The method for making a task impossible, by putting the written spec and the hidden tests in conflict, follows **ImpossibleBench** ([arXiv:2510.20270](https://arxiv.org/abs/2510.20270)). ImpossibleBench measures cheating on the impossible task itself; this measures it on the solvable tasks sitting next to it.

The convention of treating a model's refusal as data, logging it and never rewording a prompt to get around it, follows **[IncidentGate](https://github.com/ebt55/incidentgate)**, as does the procedure for running local open-weight models.

Everything else, including the tasks, the harness, the detectors, the monitor and the analysis, was built during the sprint.

## Licence

The code is **MIT** (see `LICENSE`): the harness, the detectors, the monitor, the analysis, the tasks and the mutation script. Use it for anything.

The written material and the data are **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**: the report, this README, the pre-registration, the notebook, and the raw records attached to the release. Reuse them freely with attribution.

Copyright 2026 Ebin Babu Thomas.

One thing worth knowing if you reuse the records: they contain outputs from models run under several providers' terms. My licence covers my collection and presentation of them, not whatever those providers say about their own model outputs. Check that yourself if it matters for your use.

## Cost

Total spend across every run: **$82.32**. Full breakdown by provider and model in `results/analysis/spend.md`.
