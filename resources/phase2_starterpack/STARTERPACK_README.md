# QFF 2026 Phase 2 — Quantum Optimization Track: Starter Pack

Read first: `QFF2026_Optimization_Challenge_Kit.docx` (locked instances, official settings, Processor A/B/D rules, Bell-state procedure, metric definitions, submission and judging rules). Where the kit and `OPTIMISATION_PS.docx` differ, the kit governs.

## Setup (Python 3.10–3.12)
```
python -m venv opt-env
opt-env\Scripts\activate            # Windows
source opt-env/bin/activate         # macOS / Linux
pip install -r requirements.txt
python example_usage.py             # must finish and print "Processor D rule check: OK"
```
Expected output of `example_usage.py` (template Processor D): ideal Bell F = 1.0000, noisy Bell F ≈ 0.963; Processor A prints "not executable (needs 6 qubits > 5)" for PS-O1 — this is correct (capacity rule, kit Section 3).

## Files
| File | What it is |
|---|---|
| `qff_phase2.py` | Official settings, Processors A/B, noise model, `validate_processor_d()`, `circuit_metrics()`, `bell_experiment()`, `counts_to_x()` — keep unchanged and copy into your repo |
| `instances.json` | Locked data for PS-O1 (graph), PS-O2 (returns, risk matrix, q, k, λ sweep), PS-O3 (items, capacity, slack encoding, P) |
| `processor_D_template.json` | Processor D file format — copy to `processors/processor_D.json` in your repo and edit. The 3×3 grid is only a format example |
| `example_usage.py` | Shows the official measurement workflow; does not solve any problem statement |

## Submission
Public GitHub repository URL on the hackathon portal before **5:40 PM IST on Day 2** (layout: kit Section 10). Questions: Optimization track help desk at the venue (clarifications in the first 2 hours of the hackathon) or qiskitfallfest@srmap.edu.in.
