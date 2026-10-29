#!/usr/bin/env python3
"""Repair only Markdown source cells in the saved notebook; preserve all code/results."""
from __future__ import annotations
import json
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "main.ipynb"
path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT
if not path.is_file():
    raise SystemExit(f"Notebook not found: {path}")
nb = json.loads(path.read_text(encoding="utf-8"))
original_code_cells = [
    (c.get("id"), c.get("execution_count"), c.get("outputs", []), "".join(c.get("source", [])))
    for c in nb.get("cells", []) if c.get("cell_type") == "code"
]
cover = r'''<div align="center">

<table align="center" border="0" cellpadding="6">
  <tr>
    <td align="center" valign="middle" bgcolor="#F5F1E2">
      <img src="Phase%20One/assets/branding/srm-ap-logo.png" width="150" alt="SRM University-AP">
    </td>
    <td align="center" valign="middle" bgcolor="#F5F1E2">
      <img src="Phase%20One/assets/branding/qiskit-fall-fest-2026-badge-crop.png" width="80" alt="Qiskit Fall Fest 2026">
    </td>
  </tr>
</table>

<p><sub>QFF SRM AP 2026 · QUANTUM OPTIMIZATION · PHASE 2</sub></p>
<h1>Portfolio Optimization with QAOA</h1>
<h3>PS-O2 · Constraint-Aware Portfolio Selection</h3>
<h2>✦ C O U G H I N G &nbsp; B A B Y ✦</h2>
<p><sub>TEAM PROJECT · SRM UNIVERSITY-AP × VIT-AP</sub></p>
<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Qiskit-QAOA-6929C4?style=flat-square" alt="Qiskit QAOA">
  <img src="https://img.shields.io/badge/Processor%20D-D1%20Selected-B32025?style=flat-square" alt="Processor D1 selected">
</p>

</div>

---

This notebook is the reproducible end-to-end PS-O2 run. It validates the locked inputs, displays the exact classical reference, runs the Phase 2 test suite, then generates the official Processor A/B/D results, D1 Bell verification and the full Processor D penalty sweep.

Run from the repository root. The organizer's `qff_phase2.py` and `data/instances.json` are immutable inputs.'''
patched = 0
for cell in nb.get("cells", []):
    if cell.get("cell_type") != "markdown":
        continue
    text = "".join(cell.get("source", []))
    # GitHub/Jupyter Markdown's portable math delimiters.
    text = text.replace(r"\[", "$$").replace(r"\]", "$$")
    text = text.replace(r"\(", "$").replace(r"\)", "$")
    # A prior JSON escaping defect converted the leading slash in \beta to backspace.
    text = text.replace("\x08eta", r"\beta")
    text = "".join(ch for ch in text if ch in "\n\r\t" or ord(ch) >= 32)
    if "This is the reproducible end-to-end PS-O2 run." in text or "This notebook is the executable project flow" in text or "This notebook is the reproducible" in text:
        text = cover
    if "The objective is $F(x)=" in text:
        text = r'''## 2. Locked formulation and exact classical baseline

The objective is $F(x)=\mu^{\mathsf T}x-qx^{\mathsf T}\Sigma x$, constrained to exactly two selected assets. The QUBO minimizes $-F(x)+\lambda(\sum_i x_i-2)^2$. All 16 bitstrings are enumerated; six are feasible.'''
    if "QAOA depth" in text and "initializations" in text:
        text = r'''## 3. Official settings

- QAOA depth $p=1$; five independent starts (seeds 0–4), with $\gamma,\beta\sim U[0,\pi]$.
- COBYLA, maximum 200 exact statevector objective evaluations per start.
- At reference $\lambda=2$, selected ideal angles are reused unchanged on A/B/D.
- For each required D penalty value $\lambda\in\{0,0.5,1,2,5,10\}$, all five starts are re-optimized; selected angles are then used for ideal and noisy sampling.
- 4,096 shots per condition, with official Qiskit transpiler settings and synthetic noise from unchanged `qff_phase2.py`.'''
    cell["source"] = text.splitlines(keepends=True)
    patched += 1
# Hard guard: only Markdown cells may be changed by this script.
after_code_cells = [
    (c.get("id"), c.get("execution_count"), c.get("outputs", []), "".join(c.get("source", [])))
    for c in nb.get("cells", []) if c.get("cell_type") == "code"
]
if original_code_cells != after_code_cells:
    raise SystemExit("Refusing to write notebook: code cells, execution counts or outputs changed unexpectedly")
path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"PASS notebook Markdown refresh: {patched} Markdown cells normalized; code cells and outputs preserved.")
