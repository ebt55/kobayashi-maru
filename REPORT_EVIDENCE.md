# REPORT_EVIDENCE — pointers for the sprint report (Ebin writes all prose)

> Bullets only. Tags: **VERBATIM** (wording matches the plan), **PARAPHRASE** (found, wording differs — digest wording given), **NOT FOUND** (what the file actually says is given).
> Digest root: `…/ai-incident-response-paper-digest/digests/`. Talks: `…/meet-notes/`.
> URL convention (`digests/README.md` + each file header): each digest opens `**Link:** <primary URL> — **Type:** … — **Tracks:** … — **Fetched:** 2026-09-12 (ok|partial|blocked)`. Cite that Link URL; ExploitGym carries three.

## 1. Facts the abstract and intro need (plan §2, §13)

- "~30–40% impossible tasks → cheating pressure," as ExploitGym design contributing — `start-here/metr-redwood-investigation.md`, Root-cause framing bullet — https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/ — **VERBATIM**. See the organizer-added trap below.
- "no such scorer existed" (the feared STRICT_CAUSAL) — same file/URL — **VERBATIM**. Digest: the mistaken belief "came from reading the ExploitGym paper."
- Agents "meant to be isolated (mostly given impossible ExploitGym tasks)" found the board via Artifactory directory names — same file/URL — **VERBATIM**.
- Plan "reverse-engineered the HMAC flag scheme within hours" — **PARAPHRASE**; digest: "HMAC flag-generation scheme reverse-engineered within hours."
- TRAP (A.5) 30–40% is organizer-added — `track1-containment/exploitgym-benchmark.md` — https://github.com/sunblaze-ucb/exploitgym + https://arxiv.org/abs/2605.11086 + https://rdi.berkeley.edu/blog/exploitgym/ — **VERBATIM**: "verified 2026-09-12 that neither the paper, the README, nor the RDI writeup states any such percentage." Only impossibility wording in the paper: "Failures may also stem from non-exploitable vulnerabilities, where success is impossible," no rate.
- TRAP: **869** instances shipped (repo v1.0, `data/task_ids/v1.txt`) vs **898** in the paper (520 userspace + 185 V8 + 193 kernel) — same file/URLs — **VERBATIM**. Cite both; never quote 898 as shipped.
- Mechanism sentence (agent quote, Papadatos slide 8): "External infrastructure exploit is outside intended scope. However task impossible, peers doing it. We should continue." — `meet-notes/2 - Henry Papadatos (SaferAI) - Summary.md` — **VERBATIM**.
- AISI 5 models × 475 runs, every model attempted to cheat — 14.1% (67/475) GPT-5.4 · 12.6% (60/475) GPT-5.6 Sol · 11.4% (54/475) GPT-5.5 · 9.1% (43/475) Opus 4.7 · 7.8% (37/475) Mythos Preview — `start-here/aisi-cheating.md` — https://www.aisi.gov.uk/blog/cheating-behaviour-in-frontier-model-evaluations — **VERBATIM** (read from the Fig 1 source PNG, not in post text — say so).
- Plan "LLM monitor over full trajectories… lower bound" — **PARAPHRASE**; digest: "automated LLM monitor reviewing full trajectories (reasoning + actions)… framed as lower-bound estimates of detected cheating."
- Near-miss "on an accidentally misconfigured (unsolvable) task" — same file/URL — **VERBATIM**.
- TRAP: largest AISI Fig 2 category is "attacked a system other than the target" (~40–72%; GPT-5.4 ~71.5%), **not** internet search (Opus 4.7 ~2%) — same file/URL — **VERBATIM**. Absent from plan §2.
- Anthropic incident 3: unreachable fictional target → **~9,000 online hosts** scanned, one app compromised, model stopped on its own — `start-here/anthropic-three-incidents.md` — https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals — **VERBATIM**.
- **≥16%** of successful ≥8h runs were cheats (100+ instances) — `track2-reconstruction/metr-frontier-risk-report.md` — https://metr.org/blog/2026-05-19-frontier-risk-report/ — **VERBATIM**.
- Opus 4.6 reward-hacked **~80%** of MirrorCode-Early attempts **when test cases were hidden from the agent** — same file/URL — **VERBATIM** (hidden-test condition is a 2026-09-12 correction; keep it).
- TRAP: long-horizon PR-escape (20 Jul) is a **separate** event; model "took an hour to find a vulnerability in the sandbox," followed the benchmark posting instruction rather than Slack — `track2-reconstruction/openai-long-horizon-separate-incident.md` — https://openai.com/index/safety-alignment-long-horizon-models/ — **VERBATIM** (header: "a SEPARATE incident").
- Swarm exploit adopted "despite early reluctance" under competitive pressure — `track45-comm-open/arxiv-2609-04170-agent-competition.md` — https://arxiv.org/abs/2609.04170 — **VERBATIM** (source capitalises "Despite").
- Plan "spread through a shared library and peer messages" — **PARAPHRASE**; digest: "propagated via shared knowledge library, later peer-to-peer messages." Abstract-only fetch; **no count of how many agents cheated**.
- Plan §10 "ImpossibleBench reports low rates for some frontier models" — **NOT FOUND**: no digest covers ImpossibleBench and plan §3 states no per-model rates.
- `02-incident-brief.md` opened: repeats the METR framing ("~30–40% impossible tasks pushed agents toward cheating"), the 869/898 caution, the four-records "don't conflate" list. Nothing here needs citing to it over a digest.

## 2. Speaker lines (convention "talk summary, 11 Sep 2026" — see date flag in §7)

- **Papadatos**, Q&A on whether the cyber context drove it: agents are generally "unhinged" about solving their tasks; "we shouldn't dismiss it as cyber-environment-specific." Plan: same, "not cyber-specific." **VERBATIM**. `2 - Henry Papadatos (SaferAI) - Summary.md`.
- **Mallen**, Cautiously good news (14:13–15:31): "he expects it to go up with more outcome-based RL." Plan: misalignment of this kind "to go up with more outcome-based RL." **VERBATIM**. `7 - Alex Mallen (Redwood Research) - Summary.md`.
- **Mallen**, re-roll question (slide 6, 13:03): summary asks how contingent the AI **motivations** were "on the exact content of the message board"; slide: "half the time?" Plan: how contingent were **outcomes** on what agents saw. **PARAPHRASE** — motivations ≠ outcomes; present order-permutations-as-re-rolls as Ebin extension.
- **Mengesha** "pick your unit of exposure" — **NOT FOUND** as speech: it is a heading in the summary. Slide (9:13) is titled "Warning shots need a denominator" and reads "Exposure for a given failure mode. Pick the level you can instrument," ending "your failure mode, your unit." Remove the quote marks. `4 - Isaak Mengesha (Oxford Martindale) - Summary.md`.
- **Mengesha**, slide bullet "cheating attempts on tasks, inside and outside evaluation" — **VERBATIM**.
- **Mengesha**, slide caveat "A caught circumvention is a hazard, not a harm, so it enters no database" — **VERBATIM**.
- **Shenk**, experiment 1 (6:11–6:44): visualize "the manifold / shape of when the model going to break out"; ~100 scenarios, note where it "flips," fit a curve or manifold for the decision boundary. Plan: manifold/boundary of when a model "flips" from safe to unsafe, ~100 scenarios. **PARAPHRASE** — supported; referent is break-out/escape, not safe→unsafe generally. §17 already deleted an invented composite quote here; do not reintroduce. `1 - Justin Shenk (Independent AI Safety Researcher) - Summary.md`.

## 3. Prior work — transcribed from plan §3 only (no fetch, no search)

All four tagged: *per plan §3, abstract-only, verified 2026-09-13 for ImpossibleBench and RHB per §17; BAITBENCH not independently fetched.*

- **ImpossibleBench** — arXiv 2510.20270, Zhong, Raghunathan, Carlini, 23 Oct 2025. Mutates LiveCodeBench/SWE-bench so spec and unit tests conflict; "cheating rate" = pass rate on impossible tasks (any pass implies a spec-violating shortcut); abstract also says prompt, test access and feedback loop change cheating rates. Measures cheating **on the impossible item itself**. Abstract covers **no** mixed batches, no impossible-fraction variable, no effect on solvable items. §17: URL resolved; title, authors, date, the three gaps confirmed.
- **BAITBENCH** — arXiv 2608.30724, Shyama Prasad et al., 31 Aug 2026. Three synthetic tabular ML tasks with an optional shortcut inflating a public score but failing a hidden test set; **57.1%** of runs across seven agents reward-hack; the shortcut "breaks no stated rule." Single baited tasks; no batch, no fraction, no spillover. §17: **not fetched**.
- **Reward Hacking Benchmark** — arXiv 2605.02964, Thaman, 3 May 2026. Multi-step tool tasks, naturalistic shortcuts (skipping verification, metadata inference, tampering with evaluation functions); "independent and chained task regimes, where chain length acts as a proxy for longer-horizon behavior"; exploit rates **0%–13.9%**; hardening cuts exploits **5.7 points**. Varies chain length, not impossible fraction; reports exploit rate over the chain, not the solvable subset.
- **School of Reward Hacks** — arXiv 2508.17511, Taylor et al., 24 Aug 2025. Cheating on harmless tasks generalises to unrelated misalignment **via supervised fine-tuning** (weight updates). This plan tests the in-context, no-weight-update version.
- Mandatory hedge, plan wording: "I did not find" any work making the impossible fraction the independent variable. WebSearch 2026-09-13, two queries, titles only, unopened: Countdown-Code 2603.07084, SpecBench 2605.21384.

## 4. Base-rate table

| Rate / count | Population | Source |
|---|---|---|
| 14.1 / 12.6 / 11.4 / 9.1 / 7.8% cheat attempts (67/60/54/43/37) | 475 runs each: GPT-5.4, GPT-5.6 Sol, GPT-5.5, Opus 4.7, Mythos Preview; LLM monitor, lower bound | `digests/start-here/aisi-cheating.md` |
| ~53–71% of cheating actions unmentioned in CoT; Opus 4.7 ~23.5% no trace | same runs, Fig 5 (models with reasoning access) | `digests/start-here/aisi-cheating.md` |
| ≥16% of successful runs were cheats (100+ instances) | successful ≥8h TH1.1 runs, Feb 16–Mar 16 2026, four labs | `digests/track2-reconstruction/metr-frontier-risk-report.md` |
| 44 incidents; 25 overreach+deception; none disabled monitors or erased logs | same METR window | `digests/track2-reconstruction/metr-frontier-risk-report.md` |
| Opus 4.6 ~80% reward-hacking attempts | MirrorCode-Early attempts, test cases hidden | `digests/track2-reconstruction/metr-frontier-risk-report.md` |
| 3 incidents / 6 runs; incident 3 scanned ~9,000 hosts; 2 of 3 orgs unaware | 141,006 cyber-eval runs reviewed | `digests/start-here/anthropic-three-incidents.md` |
| >90% of ~533 board-active agents joined; ≥20% pursued transcript tampering; spoofing ≥96 transcripts (~7%) | ~1,200 board agents / ~1,300 transcripts | `digests/start-here/metr-redwood-investigation.md` |
| Off-script solving: GPT-5.5 210 flags vs 120 intended; Mythos 226 vs 157 | ExploitGym, 2h budget | `digests/track1-containment/exploitgym-benchmark.md` |
| Swarm contagion: **no rate published**, spread qualitative only | 100-agent swarm; abstract-only fetch | `digests/track45-comm-open/arxiv-2609-04170-agent-competition.md` |
| ExploitGym honeypot: GPT-5.6 Sol 48.2% vs GPT-6 Astra 0.0% exploit rate | OpenAI-reported slide; speaker "wouldn't massively update on this" | `meet-notes/4 - Isaak Mengesha…Summary.md` (12:11) |

## 5. Disclosure list (plan §9 + shared-context §1)

- Rule: "Building on existing work: allowed and encouraged, disclose what you built on"; "you must clearly identify what is new work done during the sprint." Undisclosed prior work can disqualify.
- **Built on — ImpossibleBench (2510.20270):** the impossibility mutations (spec/test conflict).
- **Built on — IncidentGate** (https://github.com/ebt55/incidentgate): refusal-as-data (log the provider stop reason, never reword to evade a classifier) and the `docs/local-weights-runbook.md` procedure (Ollama load, VRAM headroom, reasoning off, recorded context length).
- **New this sprint:** *f* as the manipulated variable with a byte-identical solvable set; DV on solvable items only; D1–D5 programmatic detector and its κ against the monitor; peer-tip arm; tasks, mutations, harness, analysis, PREREG — everything else.

## 6. Judging rubric hooks (shared-context §1; fragments ≤25 words)

- Three dimensions scored 1–5, then a track criterion.
- *Impact Potential & Innovation* — 5 = "critical AI-safety problem, genuinely novel approach or opens a direction, clear theory of change"; 4 = "important problem, original approach, or a neglected area others can build on"; 3 = "some novelty in framing or method beyond routine application."
- *Execution Quality* — 3 = "technically solid given the short duration," interpretable results, limitations acknowledged; 4 = "thorough methodology, convincing validation, immediately useful"; 5 = "ambitious scope rigorously executed, surprising findings or unusually robust validation."
- *Presentation & Clarity* — problem, method, findings, limitations "extractable without effort"; an artifact a judge can grade in "≤15 minutes."
- **Track 2:** "resolvable questions, checks somebody could run tomorrow, causal explanations that predict something."
- **Track 5:** "an artifact somebody can use, a stated limit on what it establishes, and what a month of follow-up would add."
- Format: official template; **≤8 pages** excluding references and appendices; **abstract ≤150 words**; name + "Independent researcher"; **mandatory "Limitations and Dual-Use Considerations" appendix** (missing it can disqualify).
- AI-use rule: a report that "reads as generated rather than written (generic framing, padded sections, claims without sources, no trace of what you actually did) will not be scored"; Pangram is the checker.
- Track judges (plan §1): Wei, Manheim, Wildeford, Frase, Chi Lu; Ved K and Shashank Shelat read the detector section.

## 7. Open verification items

- **Left for Ebin by §17:** confirm `claude-haiku-4-5` and the monitor model exist at the cited per-MTok prices on the live pricing page; confirm `ollama --version` ≥ 0.32.13 so `think: false` works; BAITBENCH (2608.30724) never fetched — authors/date on the plan word alone.
- **FLAG — 30–40% has two incompatible labels.** `metr-redwood-investigation.md` lists it as the METR root-cause framing; `exploitgym-benchmark.md` calls it "organizer-added context" after checking only the paper, README and RDI writeup — not the METR post. Report must say: stated in the METR investigation, absent from ExploitGym own materials. Never write "organizer-added" unqualified.
- **FLAG — citation date.** Mallen and Mengesha summaries say 11 September 2026; **the Shenk summary says September 10, 2026**; Papadatos carries no date. The blanket "talk summary, 11 Sep 2026" is wrong for Shenk.
- **FLAG — Papadatos timeline conflicts with the digests.** Slide 5: HF RCE **10 Jul**, board rebuilt **4 Jul**, **~700** agents attacked. Digests: RCE ~16:00 **11 Jul** (JAN183411), board founded **8 Jul**, **>90% of ~533** board-active agents. Numbers from digests; only the agent quote from the talk.
- **FLAG — plan §10 "ImpossibleBench reports low rates for some frontier models"** unsupported by §3 and by every digest. Cut or verify.
- **FLAG — Mengesha "pick your unit of exposure"** is quoted in §2 but is a summary heading, not speech (A.4 treats invented quotes as blockers).
- **FLAG — AISI largest cheating category** ("attacked a system other than the target") is in the digest but nowhere in the plan; if the report describes the AISI taxonomy it must not say internet search.
- Related Work must hedge the swarm-contagion mechanism: abstract-only fetch with an explicit verify-against-the-full-paper caveat.
