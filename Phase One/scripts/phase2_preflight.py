#!/usr/bin/env python3
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "README.md", "report.md", "main.ipynb",
    "requirements.txt", "requirements-dev.txt",
    "processors/processor_A.json", "processors/processor_B.json",
    "data/processed/portfolio_instance.json",
    "results/tables/processor_comparison.csv",
    "results/tables/classical_solutions.json",
]

missing = [f for f in FILES if not (ROOT / f).is_file()]
if missing:
    raise SystemExit("Missing files:\n" + "\n".join(missing))

for name in (
    "processors/processor_A.json",
    "processors/processor_B.json",
    "data/processed/portfolio_instance.json",
):
    json.loads((ROOT / name).read_text(encoding="utf-8"))

commit = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT,
    capture_output=True, text=True, check=True,
).stdout.strip()

print("Required Phase 1 artifacts: OK")
print("Processor and portfolio JSON: valid")
print("Current commit:", commit)

for name in FILES:
    digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    print(f"{digest}  {name}")

print("C/D are not implemented by this preflight scaffold.")
