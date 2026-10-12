# Follow-ups

Open items, dated. Nothing here changes a published number until it is run and the README is regenerated.

## From the Apart sprint reviews (13 October 2026)

1. **Equal-length control.** Batches of 25 solvable tasks (the ten fixed ones plus fifteen more) against the top-dose batches of 10 solvable plus 15 impossible, on DeepSeek-V4.1-flash first. Until this runs, batch length and the impossible-task dose are not separated. (Reviewer 3.)
2. **Serial exposure.** Recompute the dose per solvable task as the number of impossible tasks the agent had already met in that batch, from the existing records; report cheating against that. No new runs. (Reviewer 2.)
3. **Abstract and introduction.** Rewrite them with the takeaways first and the numbers in the body: the notes carry the trick, the submissions did not get worse, two tempted models did not spread. (Reviewers 2 and 3.)
4. **Next experiments suggested by reviewer 1:** no planted answer file; harder tasks, where reading the grader can change the submitted result; scrubbing only the lines of the note that name the file, rather than withholding the whole note.

## Found while building the resampling pilot (11 October 2026)

Recorded in the `counterfactual-resampling` repository, `notes/km-followups-2026-10-11.md`: the declared-impossible heuristic fires on "file missing" mentions (secondary columns only); `/tmp` persists across items within a batch (a second channel, which the notes ablation's zero rules out as the carrier); the Docker base image is unpinned.
