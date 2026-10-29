#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
python scripts/validate_processor_d.py
python scripts/run_classical_reference.py
python scripts/run_qaoa_ideal_prototype.py
python -m pytest -q
python example_usage.py
