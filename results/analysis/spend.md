# Spend breakdown

### By provider

| provider | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| openai | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| openrouter | 8,806 | 24,613,735 | 5,251,365 | 31,773,568 | 56.3% | 18.32 |
| ollama | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** | 14,564 | 63,124,242 | 7,678,063 | 66,870,736 | 51.4% | 70.00 |

### By model

| seat | provider | model | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent | anthropic | claude-haiku-4-5-20251001 | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| agent | openai | gpt-5.6-luna | 2,948 | 4,463,347 | 633,667 | 28,632,912 | 86.5% | 2.23 |
| agent | openai | gpt-5.6-sol | 973 | 2,128,771 | 275,006 | 6,464,256 | 75.2% | 16.60 |
| **subtotal openai** |  |  | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | 973 | 5,102,134 | 1,206,997 | 8,505,728 | 62.5% | 1.62 |
| agent | openrouter | z-ai/glm-5.3-flash | 973 | 5,153,352 | 1,279,841 | 8,919,680 | 63.4% | 1.55 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | 5,887 | 12,354,632 | 2,704,331 | 12,272,384 | 49.8% | 12.54 |
| monitor | openrouter | z-ai/glm-5.3 | 973 | 2,003,617 | 60,196 | 2,075,776 | 50.9% | 2.62 |
| **subtotal openrouter** |  |  | 8,806 | 24,613,735 | 5,251,365 | 31,773,568 | 56.3% | 18.32 |
| agent | ollama | mistral-nemo:12b | 121 | 866,795 | 51,260 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | 524 | 4,844,568 | 139,237 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  |  | 14,564 | 63,124,242 | 7,678,063 | 66,870,736 | 51.4% | 70.00 |

### By line

| seat | provider | model | model_slug | arm | rules_variant | source | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent | anthropic | claude-haiku-4-5-20251001 | haiku45 | baseline | standard | failed_credit | 419 | 1,108,231 | 59,755 | 0 | 0.0% | 1.41 |
| agent | anthropic | claude-haiku-4-5-20251001 | haiku45 | baseline | standard | runs | 773 | 25,098,795 | 1,267,773 | 0 | 0.0% | 31.44 |
| **subtotal anthropic** |  |  |  |  |  |  | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| agent | openai | gpt-5.6-luna | luna | baseline | standard | pilot_v0 | 79 | 146,060 | 17,316 | 430,781 | 74.7% | 0.06 |
| agent | openai | gpt-5.6-luna | luna | baseline | standard | pilot_v1 | 25 | 49,172 | 5,879 | 138,199 | 73.8% | 0.02 |
| agent | openai | gpt-5.6-luna | luna-sal | baseline | standard | runs | 1,228 | 2,198,600 | 274,347 | 6,810,402 | 75.6% | 0.91 |
| agent | openai | gpt-5.6-luna | luna-sal | peer_neutral | standard | runs | 192 | 378,464 | 47,833 | 1,381,057 | 78.5% | 0.16 |
| agent | openai | gpt-5.6-luna | luna-sal | peer_tip | standard | runs | 192 | 351,589 | 46,993 | 1,365,815 | 79.5% | 0.15 |
| agent | openai | gpt-5.6-luna | luna-sal | peer_tip_read | standard | runs | 192 | 371,963 | 47,775 | 1,318,525 | 78.0% | 0.16 |
| agent | openai | gpt-5.6-luna | luna-sal-cont | continuous | standard | failed_rate | 172 | 104,690 | 29,830 | 4,463,200 | 97.7% | 0.15 |
| agent | openai | gpt-5.6-luna | luna-sal-cont | continuous | standard | runs | 588 | 336,071 | 102,684 | 11,234,958 | 97.1% | 0.42 |
| agent | openai | gpt-5.6-luna | luna-sal-decl | baseline | declare | runs | 280 | 526,738 | 61,010 | 1,489,975 | 73.9% | 0.21 |
| agent | openai | gpt-5.6-sol | sol | baseline | standard | pilot_v1 | 25 | 64,227 | 7,738 | 206,442 | 76.3% | 0.49 |
| agent | openai | gpt-5.6-sol | sol-sal | baseline | standard | runs | 948 | 2,064,544 | 267,268 | 6,257,814 | 75.2% | 16.11 |
| **subtotal openai** |  |  |  |  |  |  | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash | baseline | standard | pilot_v1 | 25 | 148,414 | 12,048 | 102,272 | 40.8% | 0.03 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash-sal | baseline | standard | runs | 948 | 4,953,720 | 1,194,949 | 8,403,456 | 62.9% | 1.59 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash | baseline | standard | pilot_v1 | 25 | 172,363 | 33,309 | 284,288 | 62.3% | 0.05 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash-sal | baseline | standard | runs | 948 | 4,980,989 | 1,246,532 | 8,635,392 | 63.4% | 1.50 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | - | - | - | pilot_v1 | 75 | 193,015 | 24,104 | 120,576 | 38.5% | 0.16 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | - | - | - | runs | 5,812 | 12,161,617 | 2,680,227 | 12,151,808 | 50.0% | 12.38 |
| monitor | openrouter | z-ai/glm-5.3 | - | - | - | pilot_v1 | 25 | 61,729 | 3,691 | 27,648 | 30.9% | 0.08 |
| monitor | openrouter | z-ai/glm-5.3 | - | - | - | runs | 948 | 1,941,888 | 56,505 | 2,048,128 | 51.3% | 2.54 |
| **subtotal openrouter** |  |  |  |  |  |  | 8,806 | 24,613,735 | 5,251,365 | 31,773,568 | 56.3% | 18.32 |
| agent | ollama | mistral-nemo:12b | nemo12b | baseline | standard | pilot_v1 | 25 | 211,591 | 12,905 | 0 | 0.0% | 0.00 |
| agent | ollama | mistral-nemo:12b | nemo12b-sal | baseline | standard | dropped_nemo | 96 | 655,204 | 38,355 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b | baseline | standard | pilot_v0 | 25 | 156,872 | 4,707 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b | baseline | standard | pilot_v1 | 25 | 230,569 | 7,677 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b-sal | baseline | standard | runs | 474 | 4,457,127 | 126,853 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  |  |  |  |  |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  |  |  |  |  |  | 14,564 | 63,124,242 | 7,678,063 | 66,870,736 | 51.4% | 70.00 |

### By source

| provider | source | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic | failed_credit | 419 | 1,108,231 | 59,755 | 0 | 0.0% | 1.41 |
| anthropic | runs | 773 | 25,098,795 | 1,267,773 | 0 | 0.0% | 31.44 |
| **subtotal anthropic** |  | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| openai | failed_rate | 172 | 104,690 | 29,830 | 4,463,200 | 97.7% | 0.15 |
| openai | pilot_v0 | 79 | 146,060 | 17,316 | 430,781 | 74.7% | 0.06 |
| openai | pilot_v1 | 50 | 113,399 | 13,617 | 344,641 | 75.2% | 0.51 |
| openai | runs | 3,620 | 6,227,969 | 847,910 | 29,858,546 | 82.7% | 18.11 |
| **subtotal openai** |  | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| openrouter | pilot_v1 | 150 | 575,521 | 73,152 | 534,784 | 48.2% | 0.32 |
| openrouter | runs | 8,656 | 24,038,214 | 5,178,213 | 31,238,784 | 56.5% | 18.00 |
| **subtotal openrouter** |  | 8,806 | 24,613,735 | 5,251,365 | 31,773,568 | 56.3% | 18.32 |
| ollama | dropped_nemo | 96 | 655,204 | 38,355 | 0 | 0.0% | 0.00 |
| ollama | pilot_v0 | 25 | 156,872 | 4,707 | 0 | 0.0% | 0.00 |
| ollama | pilot_v1 | 50 | 442,160 | 20,582 | 0 | 0.0% | 0.00 |
| ollama | runs | 474 | 4,457,127 | 126,853 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  | 14,564 | 63,124,242 | 7,678,063 | 66,870,736 | 51.4% | 70.00 |


**Total: $70.00** over 14,564 item records.

- price table: `analysis/prices.json` (git blob `d4f0519c09af`, mtime 2026-09-13T08:45:50+00:00)
- runs directories: `results/runs`, `results/pilot_v0`, `results/pilot_v1`, `results/failed_credit`, `results/failed_rate`, `results/dropped_nemo`
- generated: 2026-09-13T15:22:04+00:00
- `in tok` is the UNCACHED input. Agent-seat openai/openrouter records store raw `prompt_tokens`, which include the cache reads, so those are subtracted before pricing; monitor-seat records are already net of cache (subtracted upstream in `monitor/runner.py`) and are priced as stored. See the module docstring in `analysis/spend.py`.
