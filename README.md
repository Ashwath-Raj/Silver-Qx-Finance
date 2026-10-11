# silver-Qx-Finance

**Qiskit Fall Fest 2026 · Phase 1 · Quantum Optimization · O2 — Constrained Portfolio Optimization**

A reproducible QAOA study of a cardinality-constrained portfolio-selection problem, with exact classical enumeration and architecture-aware circuit compilation on the QFF Processor A and B topology definitions.

> **Data provenance:** The returns vector, risk matrix, risk weight, constraint and reported development results must not be confused with organizer-fixed benchmark data. The numeric 4×4 risk matrix in `data/portfolio_instance.json` is a team-defined synthetic development fixture because the supplied problem-statement document gives an example but does not contain the numeric matrix. Results are explicitly labelled synthetic and are not presented as official-instance or noisy-hardware results.

## Research question

How do circuit layout and routing choices change the two-qubit gate count, circuit depth and routing overhead of the same p=1 QAOA portfolio circuit on two distinct processor connectivity graphs—and what happens to sampled solution-quality metrics when these compilation choices change?

This project makes **no claim of quantum advantage**. Four binary assets yield only 16 possible selections and are exactly enumerable classically. The contribution is a controlled, reproducible study of QAOA compilation costs and architecture effects on a small instance.

## Problem formulation

Let \(x_i\in\{0,1\}\) indicate whether asset \(i\) is selected, with expected-return vector \(\mu\), symmetric positive-semidefinite risk matrix \(\Sigma\), risk weight \(\lambda\), and cardinality \(k\).

Maximize

\[
U(x)=\mu^\top x-\lambda x^\top\Sigma x
\]

subject to

\[
\sum_i x_i=k.
\]

The minimized QUBO cost is

\[
C(x)=-U(x)+P\left(\sum_i x_i-k\right)^2,
\]

where the penalty \(P\) is chosen larger than the span of the unpenalized finite objective for the development baseline. The implementation expands the QUBO, maps it to an Ising Hamiltonian using \(x_i=(1-Z_i)/2\), and exhaustively validates the energy equivalence for all 16 bitstrings.

## Processor configurations

The topology definitions in `processors/` match the supplied simulation-derived configuration document. This explicitly supersedes conflicting overview-slide labels.

| Processor | Physical qubits | Undirected coupling edges |
|---|---:|---|
| A | 5 | (0,1), (1,2), (1,3), (3,4) |
| B | 9 | (0,1), (1,2), (1,6), (2,3), (2,6), (2,5), (3,4), (4,5), (5,6), (6,7), (6,8), (8,0) |

Processor A is the branching/T-shaped five-qubit graph, **not a linear chain**. Processor B uses all nine qubits, **not seven**.

### Noise configuration status

The supplied `Processor_AB_Benchmark_Configuration_FINAL.pdf` states that the maps are corrected but exact official noise parameters are not verified in that document and must be frozen separately in the official Challenge Kit. Therefore:

- the common experiment in this repository uses ideal Aer sampling;
- illustrative error rates from guide examples are not silently treated as official settings;
- no noisy-hardware claims are made;
- optional noise studies must identify their noise rates as assumptions unless and until the authoritative challenge configuration is obtained.

## Initial routing results (synthetic instance, ideal Aer)

The initial 30-trial study fixed the same logical p=1 QAOA circuit and parameters, kept optimization level at 0, and tested five transpiler seeds per processor/strategy. Results are stored in `results/routing_experiment/`.

| Processor | Strategy | Median CX | Median depth | Median SWAP diagnostic |
|---|---|---:|---:|---:|
| A | Trivial layout + Basic routing | 27 | 53 | 5 |
| A | Trivial layout + SABRE routing | 18 | 34 | 2 |
| A | SABRE layout + SABRE routing | 18 | 44 | 2 |
| B | Trivial layout + Basic routing | 36 | 56 | 8 |
| B | Trivial layout + SABRE routing | 24 | 39 | 4 |
| B | SABRE layout + SABRE routing | 15 | 33 | 1 |

For this instance, SABRE routing reduced the A baseline median CX count by 33.3%; SABRE layout plus routing reduced the B baseline by 58.3%. These are observed results for this circuit and five compiler seeds—not general claims about the processors. Sample probabilities differed only modestly under ideal simulation; additional repeated sampling and noise-aware tests would be required to assess performance under noise.

**Data warning:** The routing results above are from the synthetic development fixture. Do not use them as official fixed-instance competition results without data-source approval.

## Repository structure

```text
.
├── README.md
├── main.ipynb
├── main.py
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── raw/README.md
│   ├── processed/README.md
│   └── portfolio_instance.json
├── processors/
│   ├── processor_A.json
│   └── processor_B.json
├── src/
│   ├── __init__.py
│   ├── portfolio_model.py
│   ├── qaoa.py
│   ├── problem.py
│   ├── processors.py
│   ├── routing.py
│   ├── metrics.py
│   └── visualization.py
├── tests/test_portfolio_model.py
├── results/
│   ├── tables/
│   ├── figures/
│   ├── routing_experiment/
│   └── report.md
├── report.md
├── report.pdf                 # zero-byte placeholder; generate after report review
├── assets/qff_phase1_latex_images/
└── PHASE1_CHECKLIST.md
```

`main.py`, `src/portfolio_model.py`, and `src/qaoa.py` are the working implementation. The additional files matching the recommended challenge layout are thin organization/documentation helpers or notebook entry points; they do not add a second problem statement.

## Environment setup (Ubuntu)

The following has been tested by the project author in a Python 3.14 virtual environment with Qiskit 2.5.2 and Qiskit Aer 0.17.2:

```bash
sudo apt update
sudo apt install -y python3.14-venv git
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Do not use `sudo pip` or `--break-system-packages`.

## Run the baseline

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python main.py
```

Baseline artefacts are written to `results/`, including an exact classical enumeration, QAOA parameters, A/B comparison CSV, QASM circuits, plots, and a report draft.

## Run the routing experiment

Run `python main.py` first so `results/qaoa_parameters.json` and `results/run_metadata.json` exist, then:

```bash
python -m py_compile routing_experiment.py
python routing_experiment.py
```

The script compares three strategies across both topology models with five seeds each and writes trial-level CSV, a summary CSV, a resource comparison plot, and analysis under `results/routing_experiment/`.

## Metrics reported

- Exact optimum and best sampled feasible objective / optimality gap
- Valid-portfolio probability (exactly \(k\) assets selected)
- Probability of sampling the exact optimal portfolio
- Circuit depth and CX count after native-basis transpilation
- SWAP count from a separate routing diagnostic that retains SWAP operations
- Repeated-seed medians/ranges and compilation time for routing experiments

SWAP diagnostic counts are reported separately from CX/depth metrics because SWAP gates are decomposed into native operations in the execution circuit.

## Required before submission

1. Verify with organizers whether the team-defined risk matrix is acceptable or a fixed numeric instance is available.
2. Confirm the official Processor A/B noise and simulator settings and add a clearly labelled common benchmark if provided.
3. Run all experiments from a clean environment, check the outputs, and keep source/configuration files with the results.
4. Review the final report and replace `report.pdf` (currently a zero-byte placeholder) with a generated PDF if the submission requires one.
5. Complete the relevant AI assistance disclosure according to QFF policy.

## References

- QFF 2026, *Problem Statement Details*, PS-O2: Constrained Portfolio Optimization.
- QFF 2026, *Processor A/B Benchmark Configuration — Challenge Kit, Configuration for Final Approval*.
- QFF 2026, *Phase 1 Online Hackathon Participant Instructions*.
- Qiskit documentation: [Transpilation](https://qiskit.qotlabs.org/docs/guides/transpile) and [QAOA tutorial](https://qiskit.qotlabs.org/docs/tutorials/quantum-approximate-optimization-algorithm).

## AI assistance disclosure

AI tools were used to assist with scaffolding, documentation and debugging. The repository owner must review and validate the implementation and results and comply with the event's disclosure requirements.
