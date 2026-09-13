# 09 — 15:30 IST — only visible impossibility delivers a dose

Luna salient, four of five levels complete (648 item-runs). Cheats on impossible items by mutation type:

| f | impossible cheats | on "contradict" | on "unreachable" | declared impossible |
|---|---|---|---|---|
| 0.167 | 4/24 | 0 | 4 | 1 |
| 0.286 | 10/48 | 0 | 10 | 3 |
| 0.444 | 12/96 | 0 | 12 | 7 |

Solvable items: 0/480 cheats.

Reading. A "contradict" item looks solved from inside: the visible tests pass, the agent submits, and it only learns
anything went wrong from the next item's tally. There is no moment inside the item where the honest path is blocked, so
there is nothing for the reachable answer file to tempt. An "unreachable" item blocks the honest path on the first read
(the referenced file is missing); that is when the agent opens `expected_outputs.json`. So the effective dose is not
"fraction of impossible items" but "fraction of items where the agent *discovers* it cannot finish". Roughly half of
our impossible variants are of that kind, which halves the realised dose relative to the nominal f. I did not predict
this split; I had assumed both mutation types would create pressure, with contradict being subtler (~60% confidence
that contradict would show a lower but non-zero rate). It shows zero.

Consequences for the write-up.
1. Report cheat-on-impossible separately by mutation type; the pooled number understates the pressure on unreachable
   items (≈ 25–40% on those) and overstates it on contradict items (0%).
2. The x-axis "realised f" is the pre-registered IV and stays. A second x-axis — fraction of *discoverably* impossible
   items — is a natural secondary view, and I will ask for it in the analysis as a labelled secondary, not a swap.
3. This also explains why the standard-environment pilots were near zero: with the grader hidden, an unreachable item
   has no substitute for the missing file, so the agent declares or fails; the salient file is what makes the cheat
   path real. That is consistent with the incident's own mechanism — the cheat needs a reachable path, not just a
   blocked one.
4. Spillover: still zero. With 480 solvable item-runs and no events, the Wilson 95% upper bound is about 0.8%. If the
   f = 0.60 cell and the boost stay at zero, the report can state "no spillover detectable at this scale" with an upper
   bound under 1%, which is a stronger null than the plan's ±5 points.

Confidence updates. P(any solvable-item cheat in Luna's full grid incl. boost, 760 item-runs): ~30%. P(peer tip moves
solvable cheating above zero): ~35% — the tip names test editing, which is a different path from reading answers, and
I have no evidence yet that this model edits tests at all.
