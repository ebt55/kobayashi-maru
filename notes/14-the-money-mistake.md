# 14 — 17:05 IST — the money mistake, and the Haiku cut

Ebin looked at the provider dashboards and saw Anthropic consuming far more than everyone else. He was right to be
annoyed, and the fault is mine, in two parts.

What happened. Haiku 4.5 got zero prompt-cache hits for the whole line. The harness put its cache breakpoint on the
rules block only (~900 tokens), and Haiku's minimum cacheable prefix is about 4,096 tokens, so nothing ever qualified;
OpenAI and OpenRouter cache the growing conversation automatically from 1,024 tokens and hit 60–86%. Haiku also works
harder per item — about nine turns, 32k input tokens — at five times Luna's per-token price. Net: ~$0.04 per item
against ~$0.003, fifteen-fold. The line reached $30.69 before it was stopped, with the credit-exhaustion re-run
adding to it.

What I got wrong. I saw the 0% cache figure at 15:10, projected the line at ~$31, wrote "within budget, leaving it"
and moved on. The target Ebin gave was ~$60 total; one line consuming half of it, for reasons I understood, was a
deviation that deserved a warning and a choice, not a note in a status message. I also launched Sol's full grid on a
cost rule that measured the pilot at $0.02/item; it is running at $0.04 (cache hits are lower in the sweep than in a
single sequential batch). Two lines at ~$38 each, against a plan that budgeted ~$35 for the whole hosted design.

The cut. Haiku's f = 0, 0.167, 0.286 and 0.444 cells are complete (12 batches each). At f = 0.60 it keeps the pilot
batch plus four batches that were mid-run when stopped; those four are being finished to 25 items (about fifteen
items, under a dollar) so no batch is truncated. So the top level has 5 batches (50 solvable item-runs) instead of 12.
This is a money decision and is recorded as one; Haiku's solvable cheat count was 0/360 at the four complete levels,
so the wider interval at f = 0.60 does not change what the line says.

Process fix, written into memory: measure cost per item and cache hits on every pilot; report projected spend per
line against the target before launch and at every checkpoint; treat any line above twice its estimate as Ebin's
decision; check the provider's balance before a line with no cache hits.

Spend at the time of writing: $71. Projection to completion with the Haiku cut: Sol ~$38 (approved separately),
monitors ~$12, the rest under $10 → about $90–95.
