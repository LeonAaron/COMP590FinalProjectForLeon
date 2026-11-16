#!/bin/bash
# Runs hidden feature tests + the app's original (regression) tests, then writes a
# partial-credit reward: hidden pass fraction x regression pass fraction.
set -uo pipefail

mkdir -p /logs/verifier
cd /tests
PYTHONPATH=/app python -m pytest -q -p no:cacheprovider -o addopts="" \
    --junitxml=/logs/verifier/junit.xml /tests
python /tests/score.py /logs/verifier/junit.xml /logs/verifier
