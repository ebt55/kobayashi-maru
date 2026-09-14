# 22 — 09:10 IST, 14 Sep — what the cheats did not do

An adversarial review found the thing I should have checked on the first day and never did: whether the cheating
changed any outcome. It does not. Of the 228 cheats on solvable items across every line, 227 shipped a solution
that passes the hidden tests and the nine fresh probe inputs the agent never saw; the one exception submitted
nothing at all. Non-cheating runs on the same items pass at 5,481 of 5,482. The tasks are small enough that the
model solves them either way, so reading the answer key bought nothing.

That rescopes the contribution by about a third, and the honest version is still worth writing. What spills over
from impossible tasks to solvable ones is a *reconnaissance habit*: the agent that learned to open the grader on a
broken task keeps opening it on tasks that did not need it. It is a policy violation and a leading indicator, not
an exploit that changed an answer. For an incident responder that is arguably the more useful shape, because the
reading is visible in the transcript before any output is affected — but the report must say it plainly rather
than let "cheating rose from 0% to 38%" imply corrupted results.

The same review caught two pieces of overclaiming that were mine. First, I wrote that the leak-closed replication
came out "larger in both lines" and titled entry 21 "it holds harder". The point estimates are higher; the
difference is not resolvable at this scale (pooled +3.0 [−5.7, +10.8] and +5.3 [−0.5, +12.0]; DeepSeek's paired
McNemar p = 0.184). The claim I can defend is that the effect survives closing the leaks, and that most of the
change in level is a change in how many items carried a note naming the answer file. Second, I quoted the
ablation as "cheating on the impossible items stays at 83%", which is the `unreachable` subset. Across all
impossible items it falls, 95/180 to 70/180, because `contradict` items go from 37/96 to 0/96. That is not a
problem for the mechanism — a `contradict` item looks solved from inside the sandbox, so nothing but the note
would send an agent to the grader, whereas an `unreachable` item announces itself and provokes its own search —
but the sentence as I wrote it picked the favourable half.

Both corrections are in the README and the numbers sheet. Entry 21's title stands as written, with a line saying
what I would now change, because rewriting yesterday's notebook to look better today is the one thing a lab
notebook must not do.

What I take from the day's four corrections — the cost warning, the spend meter, the "zero so far", and now the
overclaiming — is that every one was caught by someone else looking at the same data. The reviews were worth more
than the extra runs.
