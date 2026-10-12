# QFF 2026 Phase 1 — PS-O2 Portfolio Optimization

This repository implements the four-asset PS-O2 portfolio benchmark and a controlled Processor A/B comparison using p=1 QAOA, exact classical enumeration, QUBO/Ising validation, Qiskit transpilation, and ideal plus synthetic-noise Aer simulation.

## Repository structure

```text
project/
├── README.md
├── main.ipynb
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── processors/
│   ├── processor_A.json
│   └── processor_B.json
├── src/
│   ├── __init__.py
│   ├── problem.py
│   ├── processors.py
│   ├── routing.py
│   ├── metrics.py
│   └── visualization.py
├── results/
│   ├── tables/
│   └── figures/
├── report.md
└── assets/
    └── qff_phase1_latex_images/
```

## Authoritative input and assumptions

- The expected returns and covariance matrix are transcribed from **QFF Phase 1 Master Guide.pdf, page 4**.
- The objective is to minimize `x.T @ Sigma @ x - q * mu.T @ x`, subject to exactly two selected assets.
- The Master Guide does **not** assign a numeric `q`. Change `Q` in the first configuration cell of `main.ipynb` and document the rationale. `Q=1.0` is an example participant-selected value, not an organizer-prescribed value.
- The `A=20` cardinality penalty came from an earlier organizer clarification but is not restated in the Master Guide PS-O2 entry; its status remains disclosed in the report.
- The 5-qubit and 9-qubit coupling maps are reference architectures, not mandatory topologies.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Open `main.ipynb` from the repository root, select the `.venv` Python kernel, set `Q` in the configuration cell, and run all cells. The notebook is the end-to-end driver; there is no dependency on a separate `main.py` file.

## Reproducibility baseline

- Basis gates: `rz`, `sx`, `x`, `cx`
- Transpiler optimization level: 1
- Layout and routing: SABRE
- Transpiler seed: 42
- Shots: 4096
- QAOA depth: p=1
- Synthetic noise: single-qubit depolarizing `p=0.001`, CX depolarizing `p=0.005`, and readout error `0.01` represented as a symmetric bit-flip because the guide does not provide a readout confusion matrix.

## Outputs

- `results/tables/processor_comparison.csv`
- `results/tables/qubo_matrix.csv` and `qubo_matrix.json`
- `results/tables/classical_solutions.json`
- `results/tables/qaoa_parameters.json`
- `results/tables/run_metadata.json`
- `results/figures/` — classical portfolio, topology, and ideal/noisy output distributions
- `report.md` — provenance, metrics, interpretation, and limitations

The four-variable problem has only 16 bitstrings and is exactly enumerable classically. This is a comparison of solution quality, topology, routing, resource metrics, and synthetic-noise sensitivity; no quantum-advantage claim is made.
