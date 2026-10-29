# QFF 2026 Phase 2 — PS-O2 Initial Technical Report

## Status

This is an initial proof-of-work scaffold, not the final judged benchmark. It establishes the official locked PS-O2 data, exact classical ground truth, a checked QUBO matrix representation, a p=1 NumPy/SciPy ideal-statevector prototype, and a candidate Processor D graph. The official helper `qff_phase2.py` and locked `data/instances.json` are copied verbatim from the organizer's starter pack.

## Locked formulation

The official instance uses four binary selection variables `x_i`, expected returns `mu = [5, 3, 4, 2]`, risk-aversion parameter `q = 0.5`, and exactly `k = 2` selected assets. The return-risk objective is

`F(x) = mu^T x - q * x^T Sigma x`, subject to `sum(x) = 2`.

The penalty QUBO minimizes

`E_lambda(x) = -F(x) + lambda * (sum(x) - 2)^2`.

The official source of truth is `data/instances.json`. `data/instance.json` is a generated derived view of its PS-O2 section and must remain consistent with it.

## Exact classical reference

The code enumerates all `2^4 = 16` bitstrings, identifies the six feasible portfolios, computes each return-risk objective, and checks the symmetric QUBO matrix against the direct penalty formula for every state. For the locked instance, the exact classical optimum is `F* = 4.75`, at `x0..x3 = 1100` (asset indices 0 and 1).

The uniform-random baseline has valid-solution frequency `6/16 = 0.375` and optimal-state probability `1/16 = 0.0625`. These are baselines, not QAOA outcomes.

For the exact QUBO ground state, the minimum is infeasible at `lambda = 0` and `0.5`; it is feasible at `lambda = 1, 2, 5, 10`. This conclusion describes the exact ground state only. It does not imply that QAOA samples only feasible strings.

## Ideal statevector QAOA prototype

`src/qaoa_statevector.py` implements p=1 cost and X-mixer operations directly on a 16-amplitude NumPy statevector, then uses COBYLA to optimize the expected QUBO energy from initialization seeds 0–4. Exact statevector probabilities and deterministic 4,096-draw estimates are recorded separately.

These results test the objective/circuit loop in an ideal statevector setting. They do not involve Qiskit transpilation, the official Processor A/B/D coupling graphs, the official synthetic noise model, or quantum hardware. They cannot be used as substitutes for the required official processor benchmark.

## Candidate Processor D

The current candidate uses five physical qubits: logical variables 0–3 map to a complete K4 core, and auxiliary qubit 4 connects to core nodes 0 and 2. It is connected, contains eight undirected edges, has maximum degree four, declares the required basis gates `rz`, `sx`, `x`, `cx`, and declares the official noise floors. The K4 core is motivated by the dense pairwise interactions in the portfolio QUBO. The auxiliary qubit provides a distance-two pair for the Bell comparison.

This is a design hypothesis, not a performance conclusion. The official `validate_processor_d()` check and measured Processor A/B/D resource comparison still need to confirm the candidate is valid and whether it improves the measured bottleneck.

## Still required for the official submission

1. Run the official `validate_processor_d()` function with the required logical-qubit count.
2. Run Bell verification on an adjacent pair and a farthest pair of Processor D, ideal and noisy, and generate `results/tables/bell.csv` with correlations, fidelity and standard error.
3. Run official Qiskit-transpiled Processor A/B/D QAOA in ideal and noisy modes with the prescribed settings and at least five seeded initializations.
4. Run the full `lambda` sweep on Processor D with QAOA angles re-optimized for each value.
5. Generate the organizer-schema `results/tables/results.csv`, figures, and final report from actual benchmark runs.
6. Execute the notebook from a clean clone and reconcile every report value with generated artifacts.

## Reproducibility and limits

Use Python 3.10–3.12 as required by the starter pack. The automated tests validate the exact problem definition and internal algebra, not the uncompleted official noisy benchmark. The four-variable problem is exactly solvable classically; no quantum-advantage claim is made.
