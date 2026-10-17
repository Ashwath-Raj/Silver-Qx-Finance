#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python scripts/phase2_preflight.py
git diff --check
python -m pytest -q
