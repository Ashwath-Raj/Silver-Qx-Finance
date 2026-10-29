#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${QFF_PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  for candidate in python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$(command -v "$candidate")"; break; fi
  done
fi
if [[ -z "$PYTHON" ]] && command -v uv >/dev/null 2>&1; then
  uv python install 3.12
  PYTHON="$(uv python find 3.12)"
fi
[[ -n "$PYTHON" ]] || { echo "Python 3.10–3.12 is required; install Python 3.12 or install uv and run: uv python install 3.12" >&2; exit 1; }
"$PYTHON" - <<'PY'
import sys
if not ((3,10) <= sys.version_info[:2] <= (3,12)):
    raise SystemExit(f"QFF Phase 2 starter supports Python 3.10–3.12; found {sys.version.split()[0]}")
print("Python:",sys.version.split()[0])
PY
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest nbconvert ipykernel
python -m ipykernel install --user --name silver-qx-finance --display-name "Python (Silver Qx Finance)"
printf '
Environment ready. Activate with: source .venv/bin/activate
'
