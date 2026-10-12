# QFF 2026 Phase 1 — PS-O2 Portfolio Optimization

## Benchmark provenance

- Inputs: QFF Phase 1 Master Guide, page 4.
- Returns μ: `[0.12, 0.18, 0.1, 0.22]`
- Risk matrix minimum eigenvalue: `0.02363584`
- q: `1.0` — participant-selected because the Master Guide's PS-O2 section does not prescribe a numeric value.
- Cardinality: exactly 2 assets.
- Penalty A: `20.0`. A=20 was included in an earlier organizer clarification but is not restated in the Master Guide PS-O2 entry; verify before official submission.
- Formulation: minimize `x.T @ Sigma @ x - q * mu.T @ x + A * (sum(x)-2)^2`.
- Reported economic objective: `q * mu.T @ x - x.T @ Sigma @ x`, only on feasible portfolios.

## Exact classical reference

- Optimal portfolio: Asset_1, Asset_4
- Bitstring (asset 4 … asset 1): `1001`
- Best feasible unpenalized objective: `0.2000000000`

## Controlled Processor A/B results

| Processor | Mode | Qubits | Depth | CX | SWAP diagnostic | Valid probability | Optimal probability | Best feasible objective | Ratio | Gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Processor A | ideal | 5 | 43 | 18 | 2 | 0.7395 | 0.1221 | 0.20000000 | 1.000000 | 0.00000000 |
| Processor A | noisy | 5 | 43 | 18 | 2 | 0.6941 | 0.1130 | 0.20000000 | 1.000000 | 0.00000000 |
| Processor B | ideal | 9 | 35 | 15 | 1 | 0.7390 | 0.1277 | 0.20000000 | 1.000000 | 0.00000000 |
| Processor B | noisy | 9 | 35 | 15 | 1 | 0.6946 | 0.1208 | 0.20000000 | 1.000000 | 0.00000000 |

## Compilation protocol

- QAOA p=1; same logical circuit and optimized angles for both processors.
- Basis gates `{rz, sx, x, cx}`; optimization level 1; SABRE layout/routing; transpiler seed 42; 4096 shots.
- Noise model: one-qubit depolarizing 0.001; CX depolarizing 0.005. The guide only gives a 1% readout error rate, not a confusion matrix; this implementation models it as symmetric 1% bit-flip and records that assumption. Ideal and noisy runs are reported separately.
- SWAP count comes from a separate diagnostic transpilation with SWAP retained; it is not the native-basis circuit's literal SWAP count.

## Interpretation and limitations

- Four assets yield only 16 bitstrings and can be solved exactly classically; no quantum advantage is claimed.
- The numeric q is not specified in the Master Guide and was selected for this run; official status requires the organizers' interpretation or documented acceptance.
- Coupling graphs are reference architectures. The included A/B runs use the documented reference edges; any participant-designed topology must be reported separately.
- The synthetic noise results are Aer simulation measurements, not hardware measurements.

## Reproducibility

Run `python -m unittest discover -s tests -v`, then `python main.py --q <chosen-positive-q>`. Results are regenerated under `results/`.
