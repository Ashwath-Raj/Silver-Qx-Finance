# silver-Qx-Finance

**QFF 2026 · Phase 1 · PS-O2 — Portfolio Optimization Under Budget Constraints**

This repository implements the Master Guide's four-asset instance, builds its QUBO and Ising forms, solves the exact classical reference, runs p=1 QAOA, and evaluates the reference Processor A/B coupling graphs under a controlled Qiskit compilation baseline.

## Governing source and explicit assumptions

- The PS-O2 returns and covariance matrix are transcribed from **QFF Phase 1 Master Guide.pdf, page 4**.
- The Master Guide writes the objective as `min x.T @ Sigma @ x - q * mu.T @ x`, subject to `sum(x)=2`. It does **not** assign a numerical value to `q`. Supply `--q VALUE`; the selected value is saved in metadata and described as participant-selected, not organizer-prescribed.
- The cardinality penalty defaults to `A=20` based on the prior organizer clarification; the Master Guide's PS-O2 section does not restate a numerical penalty. Review that setting before official submission.
- Processor A uses 5 qubits and Processor B uses 9. Page 2 says the displayed coupling maps are reference architectures, not mandatory designs. This run uses the reference graphs; alternative participant-designed graphs belong in a separately labelled experiment.

## Master Guide baseline

- Basis gates: `rz`, `sx`, `x`, `cx`
- Transpiler optimization level: 1
- Layout and routing: SABRE
- Transpiler seed: 42
- Shots: 4096
- QAOA depth: p=1
- Noisy runs use single-qubit depolarizing p=0.001 and CX depolarizing p=0.005. The guide gives a 1% readout error but not a confusion matrix; this implementation uses a symmetric 1% bit-flip assumption. The ideal baseline is retained alongside the noisy run.

## Setup (Ubuntu)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Run

```bash
python main.py --q 1.0
```

`1.0` is an example participant-selected q, **not a value specified by the Master Guide**. Choose and document a justified value. The run writes `results/tables/qubo_matrix.csv`, classical enumeration, QAOA parameters, ideal/noisy A/B comparisons, figures, circuit QASM, and `report.md`.

## Evaluation and interpretation

The reported economic objective is `q * mu.T @ x - x.T @ Sigma @ x` for feasible portfolios only. The cardinality penalty is only a QUBO mechanism. Valid-solution frequency and optimal-solution frequency are separate metrics. If the classical objective is zero or negative, objective ratio is omitted and the absolute gap is reported.

The four-variable instance has 16 candidate bitstrings and is exactly enumerable classically. This is a study of solution quality, topology, routing, resource metrics, and synthetic noise—not a claim of quantum advantage.

## Reproducibility outputs

- `results/tables/qubo_matrix.csv` and `.json`
- `results/tables/processor_comparison.csv`
- `results/classical_solutions.json`
- `results/qaoa_parameters.json`
- `results/run_metadata.json`
- `results/figures/`
- `report.md` and `results/report.md`

The old synthetic run is archived separately and must not be mixed with this Master Guide run.
