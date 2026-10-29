# QFF 2026 Phase 2 — release verification status

<div align="center">
  <p><sub>PS-O2 · CONSTRAINT-AWARE PORTFOLIO SELECTION · TEAM COUGHING BABY</sub></p>
  <h2>✦ D1 SELECTED · FINAL ARTIFACTS GENERATED ✦</h2>
</div>

## Confirmed in the local project run

- The organizer's `qff_phase2.py` and locked `data/instances.json` passed SHA-256 checks before and after the final run.
- `processors/processor_D.json` contains D1, the six-qubit K4 core with a two-edge tail, and passes `validate_processor_d()`.
- **10 automated tests passed.**
- `main.ipynb` completed with all six code cells executed and no saved cell errors.
- The benchmark generated `results/tables/results.csv` (16 rows), `results/tables/bell.csv` (4 rows), `results/tables/processor_d_lambda_sweep.csv` (12 rows), and the companion condition, resource, classical-reference, QUBO, optimization-trial and metadata files.
- The reference-penalty resource comparison is A: 18 CX / depth 42 / 2 SWAPs; B: 15 CX / depth 34 / 1 SWAP; D1: 12 CX / depth 23 / 0 SWAPs.
- At the reference penalty, D1's noisy valid-solution frequency is 45.92% and optimal-portfolio probability is 24.07%. Processor B's noisy optimal probability is 24.61%, so D1 is not claimed to dominate every solution-quality metric.

## Release-hardening actions

- `scripts/plot_processor_D.py` now creates a position for every physical qubit, including D1's q5.
- The CI workflow executes the submitted notebook in a clean checkout, then validates all required run combinations and artifact consistency.
- `results/tables/results.csv` preserves the organizer's 18 required columns in order. For PS-O2, `quality_metric=valid_solution_frequency` and `quality_value` equals that value; the selected-portfolio objective ratio and uniform-random baselines are explicit extension columns.
- The technical report includes five-start exact-statevector sensitivity summaries per penalty, clearly distinguished from finite-shot noisy repetitions.

## What is not yet asserted

A green local test suite is not the same as a green GitHub Actions run. The corrective workflow must complete successfully on the pushed commit before clean-clone reproduction is described as verified. The notebook/runner uses the official synthetic noise model, not a calibrated device model. The four-variable instance has only 16 bitstrings; no quantum-advantage claim is made.

## Submission-critical constraints

Keep `qff_phase2.py` and `data/instances.json` byte-for-byte unchanged. Keep `data/instance.json` consistent with the locked PS-O2 values. `results/tables/results.csv` and `results/tables/bell.csv` are generated benchmark evidence and must not be replaced with the archived pre-D candidate table.

For the formulation, resource trade-offs, Bell results, penalty analysis and limitations, see [report.md](report.md). For setup and the artifact map, see [README.md](README.md).
