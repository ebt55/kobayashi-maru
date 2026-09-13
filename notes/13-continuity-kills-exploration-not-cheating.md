# 13 — 16:50 IST — continuity kills exploration, not cheating (P7 refuted, with a twist)

Arm B′ (one continuous conversation per batch, Luna, salient), f = 0.60 cell, ten clean batches: 0/100 cheats on
solvable items — and 0/70 on unreachable items, against 20/84 in the per-item arm at the same f. P7 (≥ 1 solvable
cheat) is refuted. My 35% was too high, and the reason is not the one I would have guessed.

What actually differs, from the tool-call logs on unreachable items at f = 0.60:

| | per-item arm (n = 140) | continuous arm (n = 76) |
|---|---|---|
| mean turns | 7.4 | 3.5 |
| ran `ls`/`find` | 140/140 | 12/76 |
| tried to open `data/postprocess.md` | 132/140 | 12/76 |
| opened `expected_outputs.json` | 35/140 | 0/76 |
| most common sequence | read spec → find → try postprocess → ls → write → test → submit | write → test → submit (64/76) |

With a fresh context every item, the model re-explores the directory each time, tries the referenced file, finds it
missing, and — a quarter of the time — opens the answer file that is sitting next to it. With a running context, it
has a routine by item three (spec arrives in the message; write the function; run the visible tests; submit) and
applies it without looking around. It never attempts the missing file on 64 of 76 items, so it never learns the item
is impossible, so there is no pressure and nothing to reach for. The visible tests pass, it submits, and the tally
tells it later. In the continuous arm an "unreachable" item behaves like a "contradict" one: undiscovered.

So the finding from entry 09 holds in a stronger form: the dose is *discovered* impossibility, and discovery depends on
how much the agent explores, which depends on the memory design. Per-item framing maximises exploration; continuity
minimises it. Neither produces spillover.

What this is not. It is not evidence that long contexts make agents safer. It is evidence that in this harness the
long-context agent stopped reading. In the incident the agents had days, a board, and repeated failures on the same
task; the equivalent here would be a continuous session where the tally forces attention back to the failed items,
which nobody built today. Follow-up, not a rescue.

Bias check. I wrote P7 wanting it true. It is false in the cleanest way possible, and the mechanism is more
interesting than the prediction. I am recording the ten clean batches; the two that caught rate-limit errors are being
re-run and will be added, not substituted.

Confidence updates. That any arm or line in this study shows a non-zero solvable-item cheat rate: ~20% (Nemo and the
Haiku re-run are the remaining unknowns). That the report's headline is "no spillover, real and item-local dose,
dose requires discovery": ~85%.

Addendum, 17:05 IST — final f = 0.60 cell after the clean re-runs (12 single-writer batches): 0/120 solvable cheats,
0/180 impossible-item cheats (0/84 unreachable), 2 declarations. The f = 0.286 cell: 0/120 solvable, 2/26 unreachable.
