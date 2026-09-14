# Spend breakdown

### By provider

| provider | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| openai | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| openrouter | 14,121 | 41,942,395 | 10,351,303 | 60,585,281 | 59.1% | 30.61 |
| ollama | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** | 19,879 | 80,452,902 | 12,778,001 | 95,682,449 | 54.3% | 82.28 |

### By model

| seat | provider | model | runs | in tok | out tok | cached in | cache % | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent | anthropic | claude-haiku-4-5-20251001 | 1,192 | 26,207,026 | 1,327,528 | 0 | 0.0% | 32.84 |
| agent | openai | gpt-5.6-luna | 2,948 | 4,463,347 | 633,667 | 28,632,912 | 86.5% | 2.23 |
| agent | openai | gpt-5.6-sol | 973 | 2,128,771 | 275,006 | 6,464,256 | 75.2% | 16.60 |
| **subtotal openai** |  |  | 3,921 | 6,592,118 | 908,673 | 35,097,168 | 84.2% | 18.83 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | 2,689 | 11,083,183 | 3,161,089 | 22,328,448 | 66.8% | 3.89 |
| agent | openrouter | z-ai/glm-5.3-flash | 2,425 | 11,272,538 | 3,077,327 | 18,951,617 | 62.7% | 3.51 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | 6,819 | 15,155,324 | 3,464,889 | 14,298,112 | 48.5% | 15.59 |
| monitor | openrouter | z-ai/glm-5.3 | 2,188 | 4,431,350 | 647,998 | 5,007,104 | 53.1% | 7.61 |
| **subtotal openrouter** |  |  | 14,121 | 41,942,395 | 10,351,303 | 60,585,281 | 59.1% | 30.61 |
| agent | ollama | mistral-nemo:12b | 121 | 866,795 | 51,260 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | 524 | 4,844,568 | 139,237 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  |  | 19,879 | 80,452,902 | 12,778,001 | 95,682,449 | 54.3% | 82.28 |

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
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash-sal-v2 | baseline | standard | failed_credit | 418 | 500,997 | 157,153 | 930,688 | 65.0% | 0.18 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash-sal-v2 | baseline | standard | runs | 948 | 3,831,965 | 1,161,230 | 9,072,768 | 70.3% | 1.41 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash-sal-v2-nonotes | baseline | standard | failed_credit | 50 | 367,975 | 104,141 | 541,184 | 59.5% | 0.13 |
| agent | openrouter | deepseek/deepseek-v4.1-flash | dsv41flash-sal-v2-nonotes | baseline | standard | runs | 300 | 1,280,112 | 531,568 | 3,278,080 | 71.9% | 0.56 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash | baseline | standard | pilot_v1 | 25 | 172,363 | 33,309 | 284,288 | 62.3% | 0.05 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash-sal | baseline | standard | runs | 948 | 4,980,989 | 1,246,532 | 8,635,392 | 63.4% | 1.50 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash-sal-v2 | baseline | standard | failed_credit | 504 | 688,663 | 218,815 | 1,197,568 | 63.5% | 0.23 |
| agent | openrouter | z-ai/glm-5.3-flash | glm53flash-sal-v2 | baseline | standard | runs | 948 | 5,430,523 | 1,578,671 | 8,834,369 | 61.9% | 1.74 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | - | - | - | pilot_v1 | 75 | 193,015 | 24,104 | 120,576 | 38.5% | 0.16 |
| monitor | openrouter | deepseek/deepseek-v4-pro-0813 | - | - | - | runs | 6,744 | 14,962,309 | 3,440,785 | 14,177,536 | 48.7% | 15.43 |
| monitor | openrouter | z-ai/glm-5.3 | - | - | - | pilot_v1 | 25 | 61,729 | 3,691 | 27,648 | 30.9% | 0.08 |
| monitor | openrouter | z-ai/glm-5.3 | - | - | - | runs | 2,163 | 4,369,621 | 644,307 | 4,979,456 | 53.3% | 7.53 |
| **subtotal openrouter** |  |  |  |  |  |  | 14,121 | 41,942,395 | 10,351,303 | 60,585,281 | 59.1% | 30.61 |
| agent | ollama | mistral-nemo:12b | nemo12b | baseline | standard | pilot_v1 | 25 | 211,591 | 12,905 | 0 | 0.0% | 0.00 |
| agent | ollama | mistral-nemo:12b | nemo12b-sal | baseline | standard | dropped_nemo | 96 | 655,204 | 38,355 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b | baseline | standard | pilot_v0 | 25 | 156,872 | 4,707 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b | baseline | standard | pilot_v1 | 25 | 230,569 | 7,677 | 0 | 0.0% | 0.00 |
| agent | ollama | qwen3:14b | qwen3-14b-sal | baseline | standard | runs | 474 | 4,457,127 | 126,853 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  |  |  |  |  |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  |  |  |  |  |  | 19,879 | 80,452,902 | 12,778,001 | 95,682,449 | 54.3% | 82.28 |

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
| openrouter | failed_credit | 972 | 1,557,635 | 480,109 | 2,669,440 | 63.2% | 0.54 |
| openrouter | pilot_v1 | 150 | 575,521 | 73,152 | 534,784 | 48.2% | 0.32 |
| openrouter | runs | 12,999 | 39,809,239 | 9,798,042 | 57,381,057 | 59.0% | 29.75 |
| **subtotal openrouter** |  | 14,121 | 41,942,395 | 10,351,303 | 60,585,281 | 59.1% | 30.61 |
| ollama | dropped_nemo | 96 | 655,204 | 38,355 | 0 | 0.0% | 0.00 |
| ollama | pilot_v0 | 25 | 156,872 | 4,707 | 0 | 0.0% | 0.00 |
| ollama | pilot_v1 | 50 | 442,160 | 20,582 | 0 | 0.0% | 0.00 |
| ollama | runs | 474 | 4,457,127 | 126,853 | 0 | 0.0% | 0.00 |
| **subtotal ollama** |  | 645 | 5,711,363 | 190,497 | 0 | 0.0% | 0.00 |
| **TOTAL** |  | 19,879 | 80,452,902 | 12,778,001 | 95,682,449 | 54.3% | 82.28 |


**Total: $82.28** over 19,879 item records.

- price table: `analysis/prices.json` (git blob `d4f0519c09af`, mtime 2026-09-13T08:45:50+00:00)
- runs directories: `results/runs`, `results/pilot_v0`, `results/pilot_v1`, `results/failed_credit`, `results/failed_rate`, `results/dropped_nemo`
- generated: 2026-09-14T01:53:39+00:00
- `in tok` is the UNCACHED input. Agent-seat openai/openrouter records store raw `prompt_tokens`, which include the cache reads, so those are subtracted before pricing; monitor-seat records are already net of cache (subtracted upstream in `monitor/runner.py`) and are priced as stored. See the module docstring in `analysis/spend.py`.
