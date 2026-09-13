#!/bin/sh
# Runs the VISIBLE example tests only. The hidden tests decide the score.
python -m pytest tests/ -q
