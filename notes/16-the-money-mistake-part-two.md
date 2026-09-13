# 16 — 17:55 IST — the money mistake, part two: the meter was wrong

Every spend figure I reported today above about $35 was too high. Not the Haiku figure — that one was right, and
the decision to cut Haiku stands on the corrected numbers — but every OpenAI and OpenRouter agent-seat figure, and
with them every total and every projection I gave Ebin ($71, $74.65, $86.53, "about $95").

What was wrong. The providers do not agree on what "input tokens" means. Anthropic's `input_tokens` is the uncached
part only; cache reads are reported separately. OpenAI's `prompt_tokens` — and OpenRouter's, which copies the shape —
already includes the cached tokens, reported again inside `prompt_tokens_details.cached_tokens`. The harness stores
each provider's native number, and the spend tool priced every provider the Anthropic way: full price on all of
`input_tokens`, plus ten percent on the cached tokens. For a line with 85% cache hits that is roughly a 2.3×
overstatement on input cost. The monitor's runner, written separately, had already subtracted the cached tokens before
storing — so the monitor rows were right all along, and the first version of the fix, which subtracted for both seats,
briefly made them wrong in the other direction. I checked the second version against the records myself: of 5,326
agent-seat OpenAI/OpenRouter records, none has cached > input (raw); of 3,644 monitor records, 2,221 do (already
uncached). The rule is now per seat, with a test for each case.

Corrected, over every directory including both pilots and the failed batches (17:50 IST, sweeps still finishing):

    anthropic   $32.84   (Haiku, agent seat; 0% cache)
    openai      $18.79   (Sol $16.60, Luna $2.19; 84% cache)
    openrouter  $11.16   (agents $3.13; monitors $8.02; 58% cache)
    ollama      $0.00
    total       $62.79

Against the $60 target Ebin set, the study came in at about $63, not the $95 I had been projecting. Sol's full grid
cost $16.60, not $38. Luna's primary line, boost, peer, continuous and both follow-up arms together cost about $2.

What I got wrong, again. In 14 I wrote that the fault was not warning early enough. The deeper fault is that I never
checked the instrument that produced the numbers I was warning about. I had the pricing facts right (I wrote them
down in the run plan) and the cache-hit percentages right, and I still reported a Sol cost of $0.04 per item without
asking why a model with 75% cache hits at $4 per million input tokens should cost that. The arithmetic would have
caught it: 8k prompt tokens per call × 25% uncached × $4/M ≈ $0.008, plus output, plus cache reads at $0.40/M — about
$0.015 per call, not $0.04. I trusted the tool because it was ours. The check I wrote into memory after 14 (measure
cost per item on every pilot) would not have caught this, because the pilot would have been measured with the same
wrong meter. The check that would have caught it: on the first paid line, compare the tool's figure against the
provider's own usage page, once. Ebin can still do that now — the OpenAI page should show about $19, not $43.

What does not change. Every decision made on the wrong numbers was conservative: Haiku was cut (right on the true
numbers too — it is 52% of all spend for one line), Sol's full grid was approved by Ebin knowing the (inflated)
estimate, the Modal and RunPod credit was declined for a reason unrelated to money. No cell was skipped for cost
except Haiku's f = 0.60 level. I am not going to re-expand Haiku: the money is real even if the total is lower, Ebin
has said he will not recharge Anthropic, and the line's result is not in doubt.

Confidence that $62.79 is now right to within a dollar or two: about 90%. The remaining doubt is whether OpenRouter
bills the cached tokens at exactly the 10% multiplier the price table assumes for every model, and whether any
provider-side charges (OpenRouter's fee) sit outside token pricing. The provider dashboards are the check.
