# Processor D Top-3 — architecture review

**Scope:** This is an interpretation of the terminal output and `summary.md` supplied for the local run. The arithmetic and graph descriptors were independently recomputed from the pasted values and edge lists. The underlying local CSV files were not available here for direct audit, and the Qiskit benchmark was not rerun in this review.

## Summary decision

**D1 (K4 core + two-edge tail) ranks first under the run's predeclared deterministic rule.** Treat it as the preferred provisional topology, not as a statistically proven performance winner. All three candidates have the same QAOA core and report identical compiled QAOA resource and portfolio metrics. The ranking is therefore driven by the farthest-pair Bell-fidelity point estimate, and the differences are smaller than the reported uncertainty.

## Topologies

![All three Processor D candidates](figures/processor_d_top3_comparison.png)

### D1 — K4 core + two-edge tail: selected by ranking rule

![D1 topology](figures/processor_d1_topology.png)

- 6 qubits, 8 couplers, diameter 3; degree sequence `(4, 3, 3, 3, 2, 1)`.
- Noisy farthest-pair Bell fidelity: `0.949097 ± 0.002450`.
- It uses the minimum coupler count among the candidates tied on QAOA metrics. Its degree-square sum is 48 (vs. 52 for D2); this is a supplemental structural heuristic, not part of the declared score.
- It ranks first because its measured farthest-pair Bell fidelity is numerically highest. The 0.000977 difference versus D2 is below the combined reported standard error.

### D2 — K4 core + two leaves: not selected, but effectively tied

![D2 topology](figures/processor_d2_topology.png)

- 6 qubits, 8 couplers, diameter 3; degree sequence `(4, 4, 3, 3, 1, 1)`.
- Noisy farthest-pair Bell fidelity: `0.948120 ± 0.002472`.
- It has the same compiled QAOA metrics, objective statistics, qubit count, and coupler count as D1. It loses only the deterministic final Bell-fidelity tie-break; the observed gap is not evidence of worse hardware/noise performance.

### D3 — K4 core + bridge + leaf: not selected

![D3 topology](figures/processor_d3_topology.png)

- 6 qubits, 9 couplers, diameter 3; degree sequence `(4, 4, 3, 3, 3, 1)`.
- Noisy farthest-pair Bell fidelity: `0.947632 ± 0.002483`.
- It adds a ninth coupler but shows no reported QAOA resource or sampling improvement. Its Bell-fidelity point estimate is lowest, but the 0.001465 gap versus D1 is also smaller than combined reported uncertainty.

## Numerical consistency check

Values reported by the local sweep:

| Metric | D1 | D2 | D3 |
|---|---:|---:|---:|
| Qubits | 6 | 6 | 6 |
| Couplers | 8 | 8 | 9 |
| Compiled CX / overhead | 12 / 0 | 12 / 0 | 12 / 0 |
| SWAPs | 0 | 0 | 0 |
| Depth / two-qubit depth | 23 / 10 | 23 / 10 | 23 / 10 |
| Noisy valid frequency | 45.9229% | 45.9229% | 45.9229% |
| Noisy optimal-solution probability | 24.0723% | 24.0723% | 24.0723% |
| Feasible-objective yield | 0.406366 | 0.406366 | 0.406366 |
| Noisy farthest-pair Bell F | 0.949097 ± 0.002450 | 0.948120 ± 0.002472 | 0.947632 ± 0.002483 |

The arithmetic checks out against the displayed values:

- Feasible-objective yield: `0.459229 × 4.203216 / 4.75 ≈ 0.406366`.
- Bell fidelity: `F = (1 + <XX> - <YY> + <ZZ>) / 4`. D1 gives `(1 + 0.934082 - (-0.921875) + 0.940430) / 4 = 0.949097` after rounding.
- The D1–D2 Bell-fidelity gap is `0.0009765`; combined reported SE is about `0.003480` (gap ≈ 0.28 combined SE). D1–D3 gap is `0.0014648`; combined reported SE is about `0.003488` (gap ≈ 0.42 combined SE). These are not statistically persuasive differences.
- The edge lists reproduce the reported degree sequences and diameters. The K4 subgraph on vertices 0–3 is identical for every candidate.

## Interpretation and limits

Because all three graphs retain the same K4 interaction core and were compiled to the same gate metrics, identical QAOA portfolio outputs are plausible and consistent with the log. The extra vertices/couplers primarily change the farthest-pair Bell test. The benchmark used one official simulator seed (42), 4,096 shots, and a uniform synthetic noise model; it does not establish performance on a calibrated physical processor or characterize crosstalk and qubit-specific errors.

**Recommendation:** keep D1 as the provisional candidate under the predeclared rule. Do not claim that D1 has statistically better Bell fidelity than D2/D3. If hardware-specific fidelity is material, run multiple seeds and/or use per-qubit and per-coupler calibrated noise before freezing D.

This is an added review document. It does not overwrite `summary.md`, change `processors/processor_D.json`, generate final Bell tables, or freeze Processor D.
