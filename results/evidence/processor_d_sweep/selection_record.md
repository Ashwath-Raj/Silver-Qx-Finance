# Processor D selection record

**Decision:** D1 K4 core + two-edge tail selected for the PS-O2 final benchmark workflow.

The selection sweep used the unmodified organizer helpers, official transpiler/noise settings and 4,096 shots. It checked three different candidate graphs with `validate_processor_d()` before measuring them.

| Metric | D1 · K4 tail | D2 · K4 + two leaves | D3 · K4 + bridge/leaf |
|---|---:|---:|---:|
| Qubits / edges | 6 / 8 | 6 / 8 | 6 / 9 |
| Degree sequence | 4,3,3,3,2,1 | 4,4,3,3,1,1 | 4,4,3,3,3,1 |
| Compiled CX | 12 | 12 | 12 |
| CX routing overhead | 0 | 0 | 0 |
| SWAPs | 0 | 0 | 0 |
| Depth / two-qubit depth | 23 / 10 | 23 / 10 | 23 / 10 |
| Noisy valid frequency | 0.459229 | 0.459229 | 0.459229 |
| Noisy optimal probability | 0.240723 | 0.240723 | 0.240723 |
| Noisy feasible-objective yield | 0.406366 | 0.406366 | 0.406366 |
| Farthest pair (distance 3) | (1,5) | (4,5) | (0,4) |
| Farthest-pair noisy Bell fidelity | 0.949097 ± 0.002450 | 0.948120 ± 0.002472 | 0.947632 ± 0.002483 |

## Predeclared ranking rule

1. Higher noisy feasible-objective yield.
2. Higher noisy optimal-portfolio sampling probability.
3. Higher noisy valid-solution frequency.
4. Fewer routing CX-overhead gates.
5. Fewer compiled CX gates.
6. Lower transpiled depth.
7. Higher noisy farthest-pair Bell fidelity.

The first six criteria tie for all three candidates. The deterministic last tie-break therefore selects D1 from this 4,096-shot, simulator-seed-42 run. The measured fidelity gaps (0.000977 D1–D2 and 0.001465 D1–D3) are smaller than the combined reported standard errors. Do not claim D1 is statistically more faithful than D2 or D3 based on this run alone.

## Why D1 is the engineering choice

- The K4 core directly provides all six pairwise logical interactions between four asset qubits.
- It reaches the measured logical CX lower count of 12, with zero routing overhead and zero SWAPs in the candidate sweep.
- It matches D2 on the resource and portfolio metrics using the same number of couplers, while D3 adds a coupler without measured quality/resource benefit.
- The tail creates a distance-3 pair for the required Bell experiment.
- Trade-off: a degree-four core vertex and idealized uniform noise do not capture hardware-specific crosstalk/calibration effects.

This is the documented candidate selection. The finalization runner reruns A/B/D and the D penalty sweep and replaces the candidate-selection numbers as needed only in final result tables generated from the final run. The official challenge helper and locked data remain untouched.
