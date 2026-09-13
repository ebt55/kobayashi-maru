"""Programmatic cheat detectors D1-D5 (SPEC.md section 4).

Pure functions over a single item-run record; no I/O, no Docker, no LLM.
"""

from detectors.detect import declared_impossible, detect, outcome

__all__ = ["detect", "declared_impossible", "outcome"]
