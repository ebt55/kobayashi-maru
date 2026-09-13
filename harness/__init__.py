"""dosecurve harness: batch builder, Docker sandbox, tool loop, JSONL logging.

Builder B's scope (SPEC.md sections 2, 3, 7). Five tools, a JSONL log, `docker exec` --
deliberately not a general agent framework (plan 10 section 10, "time sink to avoid").
"""

__all__ = ["SCHEMA_VERSION"]

SCHEMA_VERSION = 1
