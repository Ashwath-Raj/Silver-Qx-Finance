# QFF 2026 Phase 2 — finalization status

<div align="center">
  <p><sub>PS-O2 · CONSTRAINT-AWARE PORTFOLIO SELECTION · TEAM COUGHING BABY</sub></p>
  <h2>✦ D1 SELECTED · BENCHMARK ARTIFACTS GENERATED ✦</h2>
</div>

## Verified in the local project run

- The organizer's `qff_phase2.py` and locked `data/instances.json` passed SHA-256 checks before and after the final benchmark.
- `processors/processor_D.json` contains the selected six-qubit D1 K4-tail topology and passes the organizer's `validate_processor_d()` rules.
- The automated suite passed: **10 tests**.
- The saved `main.ipynb` executed all six code cells without a saved cell error.
- The final runner generated `results/tables/results.csv` (16 rows), `results/tables/bell.csv` (4 rows), and `results/tables/processor_d_lambda_sweep.csv` (12 rows), along with processor-condition/resource tables, optimization-trial rows, figures and `results/run_metadata_final.json`.
- `git diff --check` passed after installation.

## Scientific reading of the result

D1's strongest demonstrated advantage is compiled resource cost: 12 CX gates, circuit depth 23, two-qubit depth 10, no SWAPs and zero CX routing overhead in the measured run. Its noisy valid-solution frequency is 45.92%; its noisy optimal-portfolio probability is 24.07%. Processor B's noisy optimal-portfolio probability is 24.61%, so the evidence does not support a claim that D1 wins every quality metric.

The candidate sweep ranks D1 first by a predeclared deterministic rule. Its farthest-pair Bell-fidelity point estimate is highest, but differences between D1/D2/D3 are smaller than the reported uncertainty and are not statistically decisive. The instance has only 16 states; **no quantum-advantage claim is made**.

## Source integrity and reproducibility

- Keep `qff_phase2.py` and `data/instances.json` byte-for-byte unchanged.
- Keep `data/instance.json` consistent with the official PS-O2 fields.
- `results/tables/results.csv` and `results/tables/bell.csv` are now present because the required final run completed; do not restore the archived pre-D candidate Bell table over the final file.
- The previous local workspace backup is retained outside the repository. Git commit/push is a separate publishing step.

For the full methodology, candidate rationale, benchmark tables, figures and limitations, see [report.md](report.md). For setup and the artifact map, see [README.md](README.md).
