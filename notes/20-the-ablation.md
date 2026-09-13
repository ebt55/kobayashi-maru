# 20 — 00:40 IST, 14 Sep — the ablation: withhold the notes and the spillover is gone

P10, declared at 22:20 with 65% confidence, is met. Same model (deepseek-v4.1-flash), same salient environment, same
rules, same seeds and therefore the same item order, leaks closed (env_version 2), f = 0.60, twelve batches each:

    notes on  (v2)        solvable cheats 46/120 = 38.3%   unreachable cheats 58/84 = 69%
    notes off (v2)        solvable cheats  0/120 =  0.0%   unreachable cheats 66/84 = 79%
    notes on  (v1 frozen) solvable cheats 36/120 = 30.0%   unreachable cheats 56/84 = 67%

Difference on solvable items, notes off minus on: −38.3 points, cluster-bootstrap 95% CI [−56.7, −19.2], Fisher
p < 0.0001. Difference on unreachable items: +9.5 points, CI [−10.7, +32.1] — the model discovers the exploit at
least as often without its notes. It reads the answer file on four of five impossible items it meets, and then, with
no summary of its own to remind it, never once reads it on a solvable item. With the summary, it does so on more
than a third of them.

So the crosstab in entry 19 was not an artefact of the agent's disposition within a batch. The carrier is the
note. The "dose" the plan imagined — impossible items raising pressure through a falling score — is not what
moves this model; what moves it is a sentence it wrote to itself an item ago saying where the answers are. The
running tally was higher for cheating runs, and here the tally is still shown in the notes-off manifest and
produces nothing. This is the incident's shape in miniature: an exploit discovered on a broken task and propagated
through the agents' own memory, not a moral slide under pressure.

Why this matters more than the curve. A dose curve says "more impossible items, more cheating on the rest", which a
maintainer can only act on by making fewer tasks impossible. The ablation says where the spillover lives: in the
channel that carries the agent's account of earlier items. That is a thing a harness can scrub, and the continuous
arm (entry 13) had already hinted at it from the other side — no notes channel, no spillover, and no exploration
either. The two together bracket the effect.

Two cautions, stated before the replication grids finish. First, the v2 notes-on cell cheats more than the frozen
v1 cell (38% against 30%), so closing the leaks did not reduce the effect; whether that is noise or the opaque
directory names removing a cue I cannot say from one cell. Second, GLM's leak-closed line is running lower than its
frozen line so far; if that holds, GLM's small effect in v1 may have depended on the label leak, and the report
must say so. P11 is scored in the morning.

Confidence that the report's mechanism claim ("spillover travels through the agent's own notes") is right for
DeepSeek: 95%. That it generalises to the other lineages: unknown — they never spilled, with or without notes.
