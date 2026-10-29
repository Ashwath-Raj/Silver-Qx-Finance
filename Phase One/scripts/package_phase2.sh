#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

command -v zip >/dev/null || {
  echo "Install zip with: sudo apt install zip"
  exit 1
}
command -v unzip >/dev/null || {
  echo "Install unzip with: sudo apt install unzip"
  exit 1
}

mkdir -p dist

FULL="$ROOT/dist/Silver-Qx-Finance-Phase2-Prep.zip"
KIT="$ROOT/dist/QFF_Phase2_Tooling_Kit.zip"

rm -f "$FULL" "$KIT"

# Full project, excluding Git metadata, environments, caches and ZIP outputs.
zip -qr "$FULL" . \
  -x '.git/*' '*/.git/*' \
     '.venv/*' '*/.venv/*' \
     'venv/*' '*/venv/*' \
     '__pycache__/*' '*/__pycache__/*' \
     '.pytest_cache/*' '*/.pytest_cache/*' \
     '.ipynb_checkpoints/*' '*/.ipynb_checkpoints/*' \
     'dist/*' '*/dist/*' \
     '*.pyc' '*.pyo' '*.zip' \
     '.env' '.env.*' '*/.env' '*/.env.*'

# Standalone tooling ZIP, including its own packaging script.
zip -q "$KIT" \
  PHASE2_READINESS.md \
  PHASE2_PACKAGE_AUDIT.md \
  config/phase2_requirements.template.json \
  scripts/phase2_preflight.py \
  scripts/phase2_validate.sh \
  scripts/package_phase2.sh

echo "=== Verify full project ==="
unzip -t "$FULL"

echo "=== Verify tooling kit ==="
unzip -t "$KIT"

cp "$FULL" "$HOME/Downloads/"
cp "$KIT" "$HOME/Downloads/"

echo "=== Final files ==="
ls -lh "$FULL" "$KIT"
