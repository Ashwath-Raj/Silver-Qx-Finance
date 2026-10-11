#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Ashwath-Raj/silver-Qx-Finance.git"
BRANCH="main"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install with: sudo apt install git" >&2
  exit 1
fi

# Prefer GitHub CLI credentials when available; otherwise Git may use your credential helper.
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh auth setup-git >/dev/null 2>&1 || true
fi

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT
CLONE_DIR="$TMP_DIR/silver-Qx-Finance"

echo "Cloning $REPO_URL ..."
git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"

# Copy this project over the remote working tree without deleting remote-only files (e.g. LICENSE).
# Exclude any local Git metadata, virtualenv, caches, and compiled Python bytecode.
tar \
  --exclude='./.git' \
  --exclude='./.venv' \
  --exclude='*/.venv/*' \
  --exclude='*/__pycache__' \
  --exclude='*/__pycache__/*' \
  --exclude='*.pyc' \
  --exclude='*.egg-info' \
  -cf - -C "$ROOT" . | tar -xf - -C "$CLONE_DIR"

cd "$CLONE_DIR"
if ! git config user.name >/dev/null; then
  git config user.name "Ashwath Raj"
fi
if ! git config user.email >/dev/null; then
  git config user.email "214366304+Ashwath-Raj@users.noreply.github.com"
fi

git add -A
if git diff --cached --quiet; then
  echo "No changes to publish; remote repository already matches this project tree."
  exit 0
fi

git commit -m "feat: add QFF 2026 O2 portfolio QAOA Phase 1 benchmark"
git push origin "$BRANCH"
echo
echo "Push complete: https://github.com/Ashwath-Raj/silver-Qx-Finance"
echo "Existing remote-only files (including LICENSE) were preserved."
