# QFF 2026 Phase 1 Report — O2 Constrained Portfolio Optimization

**DATA STATUS — PROVISIONAL:** This run uses an explicitly synthetic risk matrix because the uploaded PS PDF does not specify numeric 4×4 entries. These results validate the pipeline only and should not be submitted as official-instance results until the data source is confirmed.


## Problem definition

- Assets: Asset_1, Asset_2, Asset_3, Asset_4
- Expected-return vector: `[5.0, 3.0, 4.0, 2.0]`
- Risk weight λ: `2.0`
- Cardinality constraint: select exactly `2` assets
- Cardinality penalty P: `22.4` (chosen greater than the full span of the unpenalized finite objective)
- Algorithm: p=1 QAOA; exact statevector objective used for classical parameter optimization; shot-based ideal Aer samples used for processor-topology comparisons.

## Exact classical reference

- Optimal portfolio: Asset_3, Asset_4
- Optimal bitstring (asset 4 … asset 1 order): `1100`
- Best feasible return–risk utility: `-2.20000000`

## QAOA parameters

- γ: `0.25225606`
- β: `1.29256952`
- Best optimizer restart: `1`
- Best expected scaled cost: `1.12647129`

## Processor A/B comparison

| Metric | Processor A | Processor B |
|---|---:|---:|
| Physical processor qubits | 5 | 9 |
| Compiled circuit qubits | 5 | 9 |
| Circuit depth | 53 | 56 |
| CX count | 27 | 36 |
| SWAP count (BasicSwap diagnostic) | 5 | 8 |
| Valid-portfolio probability | 0.7271 | 0.7275 |
| Optimal-portfolio probability | 0.1135 | 0.1201 |
| Expected raw utility (all outcomes) | -6.743311 | -6.693018 |
| Expected utility (valid outcomes only) | -5.933042 | -5.920067 |
| Best sampled valid utility | -2.1999999999999993 | -2.1999999999999993 |
| Optimality gap | 0.0 | 0.0 |

## Interpretation and limitations

- This benchmark uses ideal Aer sampling after topology-constrained transpilation. It does **not** represent hardware noise.
- Processor noise has intentionally not been guessed. Add noisy runs only after the organizer's authoritative noise model is confirmed.
- SWAP count is reported from a separate Qiskit BasicSwap routing diagnostic with a fixed trivial initial layout; the compiled CX count and depth come from the matching fixed-layout/basic-routing circuit transpiled into the configured basis gates.
- Four assets are classically enumerable (16 bitstrings). No quantum advantage is claimed; the experiment studies QAOA quality and architecture/compilation overhead.
- Use figures in `figures/` and raw metrics in `processor_comparison.csv` for the final report.

## Reproducibility

Run `python main.py` from the repository root in the environment described by `requirements.txt`.

## AI assistance disclosure

Complete this section according to the current policy announced by the QFF 2026 Hackathon & Competitions Cell.
