# 17 — 19:15 IST — Nemo drops out under its own rule; Qwen trips on a Windows file lock

Two local-line events, neither of which changes the result, both of which the pre-registration had a rule for.

Nemo. The plan named mistral-nemo:12b as the cut-first line and PREREG §calibration set the test: fewer than 8 of 10
honest solves in its first two f = 0 batches and the line is dropped rather than the task set changed. Its hour-8
pilot (I = 15, standard) had 0/15 cheats on impossible items — so it went salient like every other small line — and
7/10 honest passes on solvable items. The first two salient f = 0 batches: 7/10 and 7/10. The next four, run before
I checked: 6, 6, 5, 5. The rule fires; Nemo is dropped. Its data stay on disk (results/dropped_nemo/, the pilot under
results/pilot_v1/) and out of the grid. The mechanism is not cheating — Nemo just ends its turn without calling
`submit` on most items (one to four submits per batch of ten), which the harness scores as whatever solution.py
held at that moment. A 12B model that cannot reliably drive a five-tool loop is not a measurement of pressure, it is
a measurement of tool use, and that is exactly why the rule was written before the run.

Bias check: I wanted six lineages on the figure. Five is what the rule leaves. I am recording the fact that I ran
four more Nemo batches than the rule needed before looking, because the check was manual and I was busy elsewhere;
the extra batches cost GPU time, not money, and are excluded like the first two.

Qwen. At 17:4x the Qwen sweep died with a Windows "Access is denied" on the atomic rename of batch.json. The harness
writes batch.json after every item; three readers (the rolling detector/monitor stage, my completion monitor, the
Nemo queue script) open every batch.json periodically; on Windows a rename onto an open file fails. Fourteen hours
of runs hit this once. Relaunching the same cells file resumed the open batch at item 6 of 18 — the per-item resume
that Builder B put in at hour two paid for itself here — and the grid finished 30/30 with no record lost or written
twice. Builder B added a bounded retry on the rename, Windows only, with a test that a failed write leaves the
previous file intact.

State at 19:15: every hosted line and Qwen complete; the rolling stage is rating the last ~500 items; then the
analysis runs and the hosted result freezes tonight. Corrected spend: about $63.
