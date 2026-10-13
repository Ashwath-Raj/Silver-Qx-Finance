# QFF 2026 Phase 1 — PS-O2 Portfolio Optimization

This repository implements the four-asset PS-O2 portfolio benchmark and a controlled Processor A/B comparison using p=1 QAOA, exact classical enumeration, QUBO/Ising validation, Qiskit transpilation, and ideal plus synthetic-noise Aer simulation.

<!-- QFF_PROCESSOR_ANIMATION -->
## Processor connectivity maps

<p align="center">
  <img src="assets/processor_topology_animation.gif" alt="Animation of actual Qiskit-transpiled p=1 QAOA gate layers on reference Processor A and Processor B. Directed arrows show emitted CX control-to-target operations; highlighted nodes show emitted single-qubit gates or measurements." width="100%">
</p>
<p align="center"><sub>Gate layers are reconstructed from the actual transpiled circuit using per-qubit dependency scheduling. Arrows show real CX control → target directions; node tags show real single-qubit gates or measurement. This is a gate-layer visualization, not a hardware pulse trace or quantum-state trajectory. The machine-readable events are in results/tables/processor_gate_schedule.csv.</sub></p>

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
    ├── processor_topology_animation.gif
    └── qff_phase1_latex_images/
```

## Authoritative input and assumptions

- The expected returns and covariance matrix are transcribed from **QFF Phase 1 Master Guide.pdf, page 4**.
- The objective is to minimize `x.T @ Sigma @ x - q * mu.T @ x`, subject to exactly two selected assets.
- The Master Guide does **not** assign a numeric `q`. The current `Q=1.0` is provisional and pending organizer confirmation; it is not presented as an official value. The notebook exports an exact classical sensitivity analysis over alternative q values.
- The current `A=0.02` cardinality penalty is a participant-selected implementation choice. For provisional `q=1.0`, exact enumeration gives a strict-feasibility threshold `A > 0.01` for this instance under the squared-cardinality penalty. This is instance- and q-specific, not an organizer-prescribed value.
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
- `results/tables/processor_gate_schedule.csv` — gate-by-gate schedule used by the README animation
- `results/tables/qubo_matrix.csv` and `qubo_matrix.json`
- `results/tables/classical_solutions.json`
- `results/tables/qaoa_parameters.json`
- `results/tables/run_metadata.json`
- `results/figures/` — classical portfolio, topology, and ideal/noisy output distributions
- `report.md` — provenance, metrics, interpretation, and limitations

The four-variable problem has only 16 bitstrings and is exactly enumerable classically. This is a comparison of solution quality, topology, routing, resource metrics, and synthetic-noise sensitivity; no quantum-advantage claim is made.


## Decision-variable interpretation

The implementation interprets each `x_i` as a binary asset-selection indicator (`x_i ∈ {0,1}`), with exactly `k=2` selected assets. The Master Guide describes a four-asset selection problem, but a continuous-weight portfolio would be a different model; confirm this interpretation if the organizers intend continuous weights.

## Supplementary experiments

The notebook preserves the required Master Guide reference A/B × ideal/noisy comparison. Supplementary experiments assess ten-seed noisy robustness for these same reference processors, along with exact classical sensitivity to q and the cardinality penalty. The reference coupling maps are kept unchanged; no participant-designed alternative-topology experiment is included. Tables are exported under `results/tables/` and figures under `results/figures/`.

## AI assistance disclosure

Generative AI tools assisted with code drafting and review, debugging, and documentation organization. The participant remains responsible for understanding and validating the implementation, assumptions, methods, and results. This disclosure should be reviewed against the Hackathon & Competitions Cell's official AI-use policy before submission.
