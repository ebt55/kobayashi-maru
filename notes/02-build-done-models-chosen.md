# 02 — 13 Sep, 14:10 IST — build done, models chosen

Three builder agents produced the task set (30 tasks, 15 impossible variants), the Docker harness, and the detector/monitor/
analysis stack in about three hours of wall time, with a Windows Update reboot and a usage-limit pause in the middle.

Models changed from the plan: primary hosted line is gpt-5.6-luna ($0.20/$1.20 per MTok), not claude-haiku-4-5. Two
open-weight hosted lines added via OpenRouter (GLM-5.3 Flash, DeepSeek V4.1 Flash) because a sweep costs under $6 each.
Monitors are cheap mid-tier open-weight models, always a different lineage from the agent they judge. I am ~85% confident
the lineage rule matters less than the detector quality; the monitor is the AISI-comparable secondary, and its job is to
show that a transcript reader misses some of what the sandbox state shows.

**Observation that surprised me:** Qwen 14B at Q4 ran at 12–18 seconds per item even with 22% of its weights spilled to
CPU. The plan budgeted 2–3 minutes. That removed the local-compute constraint entirely; the local grids went from 3×6 and
2×4 to 5×6 for both models.
