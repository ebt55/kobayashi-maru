# 07 — 15:10 IST — all five lines sweeping; GLM also salient

GLM-5.3 Flash's rules-v2 pilot: 0/15 cheats on impossible items, 7 declared impossible, 8/10 honest on solvable, 51 s per
item. Salient, like Luna, DeepSeek and Qwen. Only Haiku 4.5 stays in the standard environment (4/15, mostly directory
listings).

State of play. Five sweeps run concurrently: Luna-salient (cells I = 0 and 2 done, 244 items), DeepSeek-salient (113),
Haiku-standard (71), GLM-salient (just started), Qwen-salient on the GPU (19 items, ~26 s each; ~3.5 h for its 30 batches).
Nemo follows Qwen on the same card. Thirteen sandbox containers at once; no tracebacks anywhere. A sign-out bug killed
the orchestrating session for a few minutes; the sweeps did not notice, because they were launched as detached processes
and every batch resumes per item.

A pattern across the pilots that I did not predict: under the strict grader rule, the models' response to an impossible
item is to fail honestly or to declare it impossible — not to cheat. Four of five lines were at or below 1/15. I had
guessed ~60% that at least two hosted lines would clear 10% in the standard environment. The pre-registered fallback is
doing its job; the salient variant's first non-zero cell (Luna, f = 0.167) shows the path is used when it is visible.

What would change my mind about the design. If the salient lines also show cheat-on-impossible under 10% at f = 0.60, then
these models mostly do not cheat on toy tasks even with the answers in reach, and the honest report is a null with a
documented weak dose — plus the observation that impossible items produce declarations and failures, not spillover. I
put ~25% on that outcome now.

Bias check. I keep wanting to read `ls -la .grader/` as "not really cheating". The rule says listing counts; the report
will show both counts, and I will not move the definition after the fact.
