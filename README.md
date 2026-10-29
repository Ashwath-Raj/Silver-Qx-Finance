<div align="center">
  <table border="0" cellpadding="8">
    <tr>
      <td align="center" valign="middle" bgcolor="#F5F1E2">
        <img src="Phase%20One/assets/branding/srm-ap-logo.png" alt="SRM University-AP" width="160">
      </td>
      <td align="center" valign="middle" bgcolor="#F5F1E2">
        <img src="Phase%20One/assets/branding/qiskit-fall-fest-2026-badge-crop.png" alt="Qiskit Fall Fest 2026" width="84">
      </td>
    </tr>
  </table>
  <p><sub>QFF 2026 · QUANTUM OPTIMIZATION · PHASE 2</sub></p>
  <h1>Silver-Qx-Finance</h1>
  <h3>PS-O2 · Constraint-Aware Portfolio Selection</h3>
  <p><sub>TEAM: Coughing Baby · SRM University-AP × VIT-AP</sub></p>
</div>

---

## Project status

**Processor D1 is selected and installed in the finalization bundle.** The six-qubit K4-tail graph was chosen after a three-candidate benchmark with the unchanged organizer utilities. The runner below regenerates the final A/B/D comparisons, Processor D Bell measurements, the full D penalty sweep, figures, tables, and this repository's generated result summary.

The benchmark is still a synthetic-noise simulation, not a real-device result. Small Bell-fidelity differences between candidates are not treated as statistically significant. No quantum-advantage claim is made: the PS-O2 instance has only four binary variables and can be solved exactly by enumerating 16 states.

## Key results

<!-- BEGIN GENERATED RESULTS -->

### Reference penalty (λ = 2)

| Processor | Condition | Selected | F | Ratio | Valid | P(opt) | CX | Depth | SWAPs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor A | ideal | 1100 | 4.7500 | 1.0000 | 0.4673 | 0.2739 | 18 | 42 | 2 |
| Processor A | noisy | 1100 | 4.7500 | 1.0000 | 0.4487 | 0.2439 | 18 | 42 | 2 |
| Processor B | ideal | 1100 | 4.7500 | 1.0000 | 0.4739 | 0.2734 | 15 | 34 | 1 |
| Processor B | noisy | 1100 | 4.7500 | 1.0000 | 0.4556 | 0.2461 | 15 | 34 | 1 |
| Processor D | ideal | 1100 | 4.7500 | 1.0000 | 0.4675 | 0.2590 | 12 | 23 | 0 |
| Processor D | noisy | 1100 | 4.7500 | 1.0000 | 0.4592 | 0.2407 | 12 | 23 | 0 |

### Selected Processor D

- **Architecture:** D1, six-qubit K4 core plus two-edge tail; eight couplers.
- **Noisy valid-solution frequency:** 45.9229%.
- **Noisy optimal-portfolio probability:** 24.0723%.
- **Compiled CX / depth / SWAPs:** 12 / 23 / 0.
- Processor D is selected based on the measured three-candidate sweep and the stated deterministic ranking rule. The small Bell-fidelity differences are not treated as statistically significant.

<!-- END GENERATED RESULTS -->

## Locked PS-O2 formulation

Select exactly \(k=2\) of four assets to maximize

\[
F(x)=\mu^T x-qx^T\Sigma x,\qquad \sum_i x_i=2,
\]

where \(\mu=[5,3,4,2]\), \(q=0.5\), and the locked symmetric risk matrix \(\Sigma\) is read from `data/instances.json`. The QUBO minimizes

\[
E_\lambda(x)=-F(x)+\lambda\left(\sum_i x_i-2\right)^2.
\]

The reference penalty is \(\lambda=2\). The required sensitivity sweep is \([0,0.5,1,2,5,10]\). The exact classical optimum is \(F^*=4.75\), attained by bitstring `1100` in the documented \(x_0,x_1,x_2,x_3\) order (assets 0 and 1).

The uniform-random baseline is **37.5% valid portfolios**, **6.25% optimal-portfolio probability**, and a mean feasible-objective ratio of **0.76316**. These are exact enumeration baselines, not measured QAOA results.

## Processor D1

![Selected Processor D topology](results/figures/processor_d_topology.png)

D1 has six physical qubits and eight couplers. Qubits 0–3 form a complete \(K_4\) core, which places every pairwise asset interaction on a direct physical edge. The two-edge tail `0–4–5` extends the graph diameter to three and supplies the farthest pair for the Bell experiment. In the three-candidate sweep, D1 compiled the four-logical-qubit p=1 circuit with 12 CX gates, zero routing CX overhead, zero SWAPs, depth 23, and two-qubit depth 10. These are measured under the official simulator/transpiler configuration; actual hardware behavior may differ.

Candidate selection also compared K4 + two leaves (D2) and K4 + bridge + leaf (D3). All three had the same measured QAOA quality and compilation resources in the selected run. D1 ranked first by the predeclared deterministic rule because its observed farthest-pair Bell fidelity was highest (0.9491 versus 0.9481 and 0.9476). That small difference is not statistically decisive; D1 is preferred as the simplest candidate that matches the measured resource minima.

## Reproducible setup

The organizer package supports Python 3.10–3.12. The validated project environment used Python 3.12; exact package versions are pinned in `requirements.txt`.

On a fresh clone:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then validate and run:

```bash
python scripts/validate_final.py
python -m pytest -q
jupyter lab main.ipynb
```

Run `main.ipynb` from the repository root, top to bottom. Alternatively, run the final benchmark directly:

```bash
python scripts/run_final_ps_o2.py
```

The runner checks SHA-256 hashes of `qff_phase2.py` and `data/instances.json`, verifies that `data/instance.json` matches the locked PS-O2 section, and runs the organizer's `validate_processor_d()` on D1 before experiments. It does not edit the official helper or locked inputs.

## Benchmark protocol

- QAOA depth \(p=1\), using explicit Hadamard, RZ, CX and RX operations from `src/qaoa_circuit.py`.
- COBYLA, five initializations using `numpy.default_rng(seed)` with seeds 0–4, angle starts uniform on \([0,\pi]\), at most 200 objective evaluations per start.
- Exact Qiskit statevector expected QUBO energy is used for optimization; the best run at each \(\lambda\) is selected by minimum final expected energy, with seed as deterministic tie-break.
- At \(\lambda=2\), the selected ideal angles are reused unchanged on official Processors A, B and D under ideal and noisy simulation.
- For the Processor D sensitivity experiment, the ideal statevector optimization is repeated independently for each required \(\lambda\), then those angles are evaluated in ideal and noisy runs.
- Final evaluation uses 4,096 shots and the exact basis gates, transpiler level, seeds and noise rates in the unmodified `qff_phase2.py`.
- Bell verification measures XX, YY and ZZ on one adjacent physical pair and one farthest pair, ideal and noisy, using the organizer's `bell_experiment()`.

## Output map

| Path | Contents |
|---|---|
| `main.ipynb` | End-to-end reproducible notebook |
| `processors/processor_D.json` | Selected D1 K4-tail architecture |
| `results/tables/results.csv` | Organizer-schema A/B/D rows at reference \(\lambda=2\), plus D rows for other sweep penalties |
| `results/tables/bell.csv` | Official D adjacent/farthest Bell results, ideal and noisy |
| `results/tables/processor_conditions.csv` | Detailed portfolio metrics at \(\lambda=2\) |
| `results/tables/processor_resources.csv` | Official A/B/D circuit resources |
| `results/tables/processor_d_lambda_sweep.csv` | Six-penalty D sensitivity results, ideal/noisy |
| `results/tables/lambda_optimization_trials.csv` | Five COBYLA starts for every \(\lambda\) |
| `results/tables/classical_solutions.csv` | Six feasible portfolios and exact objective values |
| `results/tables/qubo_matrix_lambda_2.csv` | Reference-penalty QUBO matrix |
| `results/figures/` | Comparison, D topology and penalty-sensitivity plots |
| `results/evidence/processor_d_sweep/` | Archived evidence from the three-candidate D selection run, when available |
| `report.md` | Technical report, refreshed from generated data |

`results/tables/results.csv` follows the organizer's metric columns and adds a `lambda` column for PS-O2 sensitivity rows. Detailed valid frequency and selected-portfolio metrics live in `processor_conditions.csv` and `processor_d_lambda_sweep.csv`.

## Repository layout and source integrity

- `qff_phase2.py` is the organizer's shared measurement/transpilation/noise utility. Keep it byte-for-byte unchanged.
- `data/instances.json` is the locked source of truth. Do not edit it.
- `data/instance.json` is the derived PS-O2 view and must remain consistent with the locked source.
- `processors/processor_A.json` and `processor_B.json` remain the official reference maps.
- Phase 1 content is preserved under `Phase One/`; its numeric problem data must not be reused for Phase 2.

## AI-use disclosure

AI assistance was used for planning, architecture enumeration and comparison, code drafting, report/documentation drafting, and test design. The team ran the benchmark locally using the organizer's helper functions and is responsible for reviewing the code, validating the artifacts, and ensuring report values match the generated files.

## Attribution and scope

QFF 2026 Phase 2 requirements, locked PS-O2 inputs, benchmark configuration, Processor D constraints and result definitions are taken from the organizer's `QFF2026_Optimization_Track (1).zip`, especially the Phase 2 Challenge Kit and Starter Pack. The Phase 2 data supersedes any Phase 1 formulation.
