# Temporary Processor D Candidate Sweep

## Status and scope

This report compares three distinct top-ranked PS-O2 K4-core candidates in the temporary `tmp/processor_d_sweep/` workspace. The official `qff_phase2.py` helpers, official basis, transpiler settings, simulator seed, noise model and 4096 shots are used unchanged. The same gamma/beta pair from the executed pre-D notebook is reused for all candidates.

**No official project file was changed by the runner.** In particular, this script does not write `processors/processor_D.json`, `results/tables/results.csv`, or the final official `results/tables/bell.csv`. The output candidate is only a recommendation and is not frozen.

## Predeclared selection rule

Rank first by noisy feasible-objective yield = (sum of objective F(x) over feasible shots) / (shots × exact classical optimum F*). Invalid shots contribute zero. This jointly rewards producing feasible portfolios and selecting higher-return feasible portfolios. Break exact ties by higher noisy optimal-portfolio probability, higher noisy valid-solution frequency, fewer compiled CX-overhead gates, fewer compiled CX gates, lower transpiled depth, then higher noisy farthest-pair Bell fidelity. This is deterministic but remains a single-seed, 4096-shot synthetic-noise comparison rather than a statistical significance test.

## Ranking

| Rank | Candidate | Qubits | Edges | Noisy feasible-objective yield | Noisy P(opt) | Noisy valid frequency | Compiled CX | CX overhead | SWAPs | Depth | Farthest Bell F (noisy) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | D1_K4_TAIL_6Q | 6 | 8 | 0.406366 | 0.240723 | 0.459229 | 12 | 0 | 0 | 23 | 0.949097 |
| 2 | D2_K4_TWO_LEAVES_6Q | 6 | 8 | 0.406366 | 0.240723 | 0.459229 | 12 | 0 | 0 | 23 | 0.948120 |
| 3 | D3_K4_BRIDGE_LEAF_6Q | 6 | 9 | 0.406366 | 0.240723 | 0.459229 | 12 | 0 | 0 | 23 | 0.947632 |

**Current measured winner:** `D1_K4_TAIL_6Q`. This selection is based on this run's finite-shot results only; inspect `candidate_conditions.csv`, `candidate_resources.csv`, and `candidate_bell.csv` before freezing any design.

## Condition metrics

| Candidate | Condition | Valid frequency | P(opt) | Mean F among valid | Feasible-objective yield | CX | CX overhead | SWAPs | Depth |
|---|---|---|---|---|---|---|---|---|---|
| D1_K4_TAIL_6Q | ideal | 0.467529 | 0.259033 | 4.253264 | 0.418637 | 12 | 0 | 0 | 23 |
| D1_K4_TAIL_6Q | noisy | 0.459229 | 0.240723 | 4.203216 | 0.406366 | 12 | 0 | 0 | 23 |
| D2_K4_TWO_LEAVES_6Q | ideal | 0.467529 | 0.259033 | 4.253264 | 0.418637 | 12 | 0 | 0 | 23 |
| D2_K4_TWO_LEAVES_6Q | noisy | 0.459229 | 0.240723 | 4.203216 | 0.406366 | 12 | 0 | 0 | 23 |
| D3_K4_BRIDGE_LEAF_6Q | ideal | 0.467529 | 0.259033 | 4.253264 | 0.418637 | 12 | 0 | 0 | 23 |
| D3_K4_BRIDGE_LEAF_6Q | noisy | 0.459229 | 0.240723 | 4.203216 | 0.406366 | 12 | 0 | 0 | 23 |

## Bell metrics

| Candidate | Pair type | Physical pair | Condition | Distance | XX | YY | ZZ | Bell fidelity | Fidelity SE |
|---|---|---|---|---|---|---|---|---|---|
| D1_K4_TAIL_6Q | adjacent | [0, 1] | ideal | 1 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D1_K4_TAIL_6Q | adjacent | [0, 1] | noisy | 1 | 0.945801 | -0.952148 | 0.955078 | 0.963257 | 0.002092 |
| D1_K4_TAIL_6Q | farthest | [1, 5] | ideal | 3 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D1_K4_TAIL_6Q | farthest | [1, 5] | noisy | 3 | 0.934082 | -0.921875 | 0.940430 | 0.949097 | 0.002450 |
| D2_K4_TWO_LEAVES_6Q | adjacent | [0, 1] | ideal | 1 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D2_K4_TWO_LEAVES_6Q | adjacent | [0, 1] | noisy | 1 | 0.945801 | -0.952148 | 0.955078 | 0.963257 | 0.002092 |
| D2_K4_TWO_LEAVES_6Q | farthest | [4, 5] | ideal | 3 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D2_K4_TWO_LEAVES_6Q | farthest | [4, 5] | noisy | 3 | 0.931641 | -0.923340 | 0.937500 | 0.948120 | 0.002472 |
| D3_K4_BRIDGE_LEAF_6Q | adjacent | [0, 1] | ideal | 1 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D3_K4_BRIDGE_LEAF_6Q | adjacent | [0, 1] | noisy | 1 | 0.945801 | -0.952148 | 0.955078 | 0.963257 | 0.002092 |
| D3_K4_BRIDGE_LEAF_6Q | farthest | [0, 4] | ideal | 3 | 1.000000 | -1.000000 | 1.000000 | 1.000000 | 0.000000 |
| D3_K4_BRIDGE_LEAF_6Q | farthest | [0, 4] | noisy | 3 | 0.932617 | -0.919434 | 0.938477 | 0.947632 | 0.002483 |

## Candidate edge lists

### D1_K4_TAIL_6Q

- Qubits: 6
- Couplers: 8
- Edges: `[[0,1],[0,2],[0,3],[0,4],[1,2],[1,3],[2,3],[4,5]]`
- Rationale: Rank-1 structural candidate: the four-qubit K4 core directly supports all six pairwise QUBO interactions, and a two-edge tail provides diameter 3 for a farthest-pair Bell test using only six physical qubits and eight couplers.

### D2_K4_TWO_LEAVES_6Q

- Qubits: 6
- Couplers: 8
- Edges: `[[0,1],[0,2],[0,3],[0,4],[1,2],[1,3],[1,5],[2,3]]`
- Rationale: Rank-3 non-isomorphic structural candidate: it retains the K4 interaction core and diameter 3 but distributes the two extra vertices as separate leaves. It tests whether a different degree distribution and farther-pair placement changes official transpilation or noisy metrics.

### D3_K4_BRIDGE_LEAF_6Q

- Qubits: 6
- Couplers: 9
- Edges: `[[0,1],[0,2],[0,3],[1,2],[1,3],[1,5],[2,3],[2,5],[4,5]]`
- Rationale: Rank-5 non-isomorphic structural candidate: it keeps a K4 core, but adds one physical vertex coupled to two core nodes and a leaf. The extra coupler may offer routing/layout flexibility; the benchmark will establish whether that flexibility offsets the additional edge.

## Reproducibility metadata

- Python executable: `/home/ashwathraj/Acadimics/3.Semister3/Hackthons/Certificate/QFF IBM  singularity/Silver-Qx-Finance/.venv/bin/python`
- Qiskit version: `2.6.1`
- Qiskit Aer version: `0.18.2`
- QAOA p=1 reference lambda: `2.0`
- Reused gamma: `3.108236020048`; beta: `0.699805426888`
- Official shots per condition/observable: `4096`
- Official transpiler/simulator seed: `42`
- Runtime seconds (excludes environment startup): `1.009`
- Organizer source hashes were rechecked before measurement.
- All three candidates were passed through `validate_processor_d` before benchmarking.

## Caution

The official noise model is uniform synthetic noise; it does not include device-specific coupler calibration, crosstalk, or qubit-specific error rates. A single official-seed run is useful for a comparable protocol benchmark, but small differences should not be described as statistically significant. Review the full CSVs and approve/freeze a design explicitly in a later step.
