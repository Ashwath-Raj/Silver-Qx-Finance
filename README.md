<div align="center">

<table align="center" border="0" cellpadding="6">
  <tr>
    <td align="center" valign="middle" bgcolor="#F5F1E2">
      <img src="assets/branding/srm-ap-logo.png" alt="SRM University-AP" width="165">
    </td>
    <td align="center" valign="middle" bgcolor="#F5F1E2">
      <img src="assets/branding/qiskit-fall-fest-2026-badge-crop.png" alt="Qiskit Fall Fest 2026" width="82">
    </td>
  </tr>
</table>

<p><sub>QFF SRM AP 2026 · QUANTUM OPTIMIZATION</sub></p>

<h1>Portfolio Optimization with QAOA</h1>
<h3>PS-O2 · Phase 1 Benchmark</h3>

<h2>✦ C O U G H I N G &nbsp; B A B Y ✦</h2>

<p><sub>TEAM PROJECT · SRM UNIVERSITY-AP × VIT-AP</sub></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Qiskit-QAOA-6929C4?style=flat-square" alt="Qiskit QAOA">
  <img src="https://img.shields.io/badge/License-Apache%202.0-2F6F44?style=flat-square" alt="Apache 2.0 License">
</p>

<p>
  <img src="assets/processor_topology_animation.gif" alt="Animated QAOA gate schedule comparing reference Processor A and Processor B" width="100%">
</p>

<p><sub>Actual Qiskit-transpiled gate activity · Reference Processor A vs Processor B</sub></p>

</div>
---

## At a glance

| Item | Result |
|---|---|
| Exact classical optimum | **Asset 1 + Asset 4** |
| Optimal bitstring | <code>1001</code> (bit order: Asset 4 … Asset 1) |
| Best feasible utility at the current provisional parameters | **0.20** |
| Algorithm | QAOA, depth \(p=1\) |
| Processor comparison | Reference Processor A (5 qubits) vs Processor B (9 qubits) |
| Validation | All 16 possible bitstrings enumerated exactly; QUBO/Ising consistency checks and automated tests |

This is a small, controlled optimization study—not a claim of quantum advantage. Because the four-variable problem has only 16 possible bitstrings, its optimum is accessible by exact classical enumeration.

## Baseline results

The same logical QAOA circuit and optimized angles are used for both processor configurations. Each probability below comes from 4,096 simulator shots.

| Processor | Mode | Qubits | Depth | CX gates | SWAP diagnostic* | Valid portfolio | Optimal portfolio |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Ideal | 5 | 43 | 18 | 2 | 53.96% | 14.40% |
| A | Synthetic noise | 5 | 43 | 18 | 2 | 52.66% | 13.38% |
| B | Ideal | 9 | 35 | 15 | 1 | 54.03% | 14.55% |
| B | Synthetic noise | 9 | 35 | 15 | 1 | 52.66% | 14.01% |

<sub>*The SWAP diagnostic comes from a separate diagnostic transpilation that retains SWAP operations; it is not the literal SWAP count of the native-basis circuit.</sub>

In this instance, Processor B compiles to a shallower circuit with fewer CX gates and has a slightly higher noisy optimal-portfolio probability. The supplementary ten-seed comparison is more cautious: the 95% paired t-intervals for all three reported metrics include zero, so these runs do not establish a statistically clear performance difference.

See [report.md](report.md) for the full results, robustness intervals, sensitivity analyses, and limitations.

## Custom PACA topology experiments (supplementary)

The Master Guide reference A/B × ideal/noisy table above remains the primary benchmark. PACA-5 and PACA-9 preserve their respective 5- and 9-qubit budgets but change the coupling graphs; they are participant-designed alternatives, not official reference processors. For each custom graph, the notebook compares the automatic SABRE layout with a fixed layout that maps logical qubits 0–3 to physical nodes 0–3, the K4 core. This is a controlled placement diagnostic, not a promise that fixed placement will always be better.

After running the notebook, inspect [topology_experiment.csv](results/tables/topology_experiment.csv) for the reference-versus-custom baseline and [paca_layout_comparison.csv](results/tables/paca_layout_comparison.csv) for automatic-versus-fixed K4 placement. The matching figure is [paca_layout_comparison.png](results/figures/paca_layout_comparison.png). Circuit depth and CX count measure compiled resource cost; valid-portfolio and optimal-portfolio probabilities measure different aspects of sampled solution quality. Interpret them separately.

| Processor | Topology | Mode | Edges | Depth | CX gates | Valid portfolio probability | Optimal portfolio probability |
|---|---|---|---:|---:|---:|---:|---:|
| A | Master Guide reference | Ideal | 4 | 43 | 18 | 53.96% | 14.40% |
| A | Master Guide reference | Noisy | 4 | 43 | 18 | 52.66% | 13.38% |
| A | PACA-5, automatic SABRE | Noisy | 8 | 24 | 12 | 52.69% | 13.11% |
| B | Master Guide reference | Ideal | 12 | 35 | 15 | 54.03% | 14.55% |
| B | Master Guide reference | Noisy | 12 | 35 | 15 | 52.66% | 14.01% |
| B | PACA-9, automatic SABRE | Noisy | 16 | 24 | 12 | 53.49% | 13.75% |

The table above reproduces the current automatic-layout baseline results. The fixed K4-core layout runs are recorded separately in `paca_layout_comparison.csv` so their measured values can be checked without overwriting the required baseline.

### Measured automatic vs fixed K4-core layout results

| Custom topology | Mode | Layout strategy | Depth | CX gates | Valid portfolio probability | Optimal portfolio probability |
|---|---|---|---:|---:|---:|---:|
| PACA-5 | Ideal | Automatic SABRE | 24 | 12 | 54.05% | 13.87% |
| PACA-5 | Ideal | Fixed K4-core [0,1,2,3] | 24 | 12 | 54.42% | 14.26% |
| PACA-5 | Noisy | Automatic SABRE | 24 | 12 | 52.69% | 13.11% |
| PACA-5 | Noisy | Fixed K4-core [0,1,2,3] | 24 | 12 | 53.49% | 13.75% |
| PACA-9 | Ideal | Automatic SABRE | 24 | 12 | 54.42% | 14.26% |
| PACA-9 | Ideal | Fixed K4-core [0,1,2,3] | 24 | 12 | 54.42% | 14.26% |
| PACA-9 | Noisy | Automatic SABRE | 24 | 12 | 53.49% | 13.75% |
| PACA-9 | Noisy | Fixed K4-core [0,1,2,3] | 24 | 12 | 53.49% | 13.75% |

## Problem formulation

Each decision variable represents whether an asset is selected:

<p align="center"><img src="assets/equations/decision_variables.png" alt="Binary selection variables with exactly two assets selected" width="100%"></p>

The implemented QUBO objective is

<p align="center"><img src="assets/equations/qubo_objective.png" alt="QUBO objective with return, risk, and cardinality penalty terms" width="100%"></p>

The reported economic utility for feasible portfolios is

<p align="center"><img src="assets/equations/economic_utility.png" alt="Economic utility equals expected return contribution minus portfolio risk" width="100%"></p>

The expected-return vector and covariance matrix are transcribed from **QFF SRM APPhase 1 Master Guide.pdf, page 4**. The numeric \(q\) and penalty \(A\) are experiment settings, not official values prescribed by the guide.

Exact classical enumeration identifies **Asset 1 and Asset 4** as the optimal feasible portfolio at the current provisional parameters:

<p align="center">
  <img src="assets/equations/exact_optimum.png" alt="Exact optimum: select Asset 1 and Asset 4, utility 0.20" width="100%">
</p>

## Method

1. **Define the instance.** Load the four-asset returns and covariance matrix and encode the exactly-two-assets constraint.
2. **Validate classically.** Enumerate all 16 bitstrings, compute the feasible optimum, and validate the QUBO/Ising formulation.
3. **Build and compile QAOA.** Run the required \(p=1\) baseline against the documented reference maps. Separately evaluate PACA custom maps using automatic SABRE layout and a fixed mapping of the four logical variables to the physical K4 core.
4. **Simulate ideal and noisy cases.** Record feasibility, optimal-solution probability, utility, depth, CX count, and a separately computed SWAP diagnostic.
5. **Test robustness and sensitivity.** Compare ten fixed simulator seeds for both reference and custom topologies, compare automatic and K4-core-constrained layouts on PACA graphs, and perform exact classical sensitivity analyses for \(q\) and \(A\).

## Reproducibility

### Environment

Python 3.12 is used in the automated workflow.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Open [main.ipynb](main.ipynb) from the repository root, select the <code>.venv</code> kernel, review the configuration cell, and run all cells. The notebook is the end-to-end experiment driver; a separate <code>main.py</code> is not required.

### Transpilation and noise settings

| Setting | Value |
|---|---|
| QAOA depth | \(p=1\) |
| Basis gates | <code>rz</code>, <code>sx</code>, <code>x</code>, <code>cx</code> |
| Optimization level | 1 |
| Layout/routing | SABRE |
| Transpiler seed | 42 |
| Shots per baseline run | 4,096 |
| Single-qubit depolarizing error | 0.001 |
| CX depolarizing error | 0.005 |
| Readout error | 0.01, represented as a symmetric bit-flip |

The guide specifies a 1% readout error rate but does not provide a readout confusion matrix. The symmetric bit-flip model is therefore an explicit simulation assumption, not an organizer-supplied calibration.

## Key assumptions and limitations

- **\(q=1.0\) is provisional.** The Master Guide's PS-O2 section does not prescribe a numeric \(q\). The repository includes exact sensitivity analysis over alternative values; organizer confirmation is needed before describing \(q=1.0\) as official.
- **\(A=0.02\) is participant-selected.** Under the current \(q\) and squared-cardinality penalty, exact enumeration gives a strict-feasibility threshold of \(A>0.01\) for this particular instance. This is not a universal or organizer-prescribed threshold.
- **Decision variables are binary.** The model selects exactly two assets; it is not a continuous-weight portfolio allocation.
- **Reference maps remain the required baseline.** PACA-5 and PACA-9 are separately labelled participant-designed supplementary graphs. Their extra edges are evaluated empirically and do not imply better solution quality.
- **Noise results are simulated.** Aer results are not measurements from quantum hardware. Ten seeds provide a limited simulator robustness check, not evidence of hardware uncertainty or broad generalization.
- **No quantum-advantage claim is made.** Exact enumeration is the appropriate classical reference for this 16-state instance.

## Repository map

| Path | Purpose |
|---|---|
| [main.ipynb](main.ipynb) | End-to-end reproducible benchmark and sensitivity analyses |
| [processors/](processors/) | Processor A and B reference configurations |
| [src/](src/) | Problem formulation, topology handling, routing, metrics, and visualization code |
| [data/](data/) | Raw and processed experiment inputs |
| [results/tables/](results/tables/) | CSV/JSON metrics, solutions, metadata, robustness and gate-schedule exports |
| [results/figures/](results/figures/) | Comparison and sensitivity figures |
| [report.md](report.md) | Full methodology, benchmark results, interpretation, and limitations |
| [tests/](tests/) | Unit and artifact checks |
| [requirements.txt](requirements.txt) | Runtime dependencies |
| [requirements-dev.txt](requirements-dev.txt) | Development and test dependencies |

### Useful result files

- [processor_comparison.csv](results/tables/processor_comparison.csv) — Processor A/B ideal and noisy baseline metrics
- [classical_solutions.json](results/tables/classical_solutions.json) — all bitstrings and exact optimum
- [processor_gate_schedule.csv](results/tables/processor_gate_schedule.csv) — events used in the gate animation
- [paired_robustness_comparison.csv](results/tables/paired_robustness_comparison.csv) — paired ten-seed Processor B minus A comparisons
- [q_sensitivity.csv](results/tables/q_sensitivity.csv) and [penalty_sensitivity.csv](results/tables/penalty_sensitivity.csv) — exact parameter sensitivity tables

---

## ✦ C O U G H I N G &nbsp; B A B Y ✦

<p><sub>QFF SRM AP 2026 · QUANTUM OPTIMIZATION · PS-O2</sub></p>

| Team member | Role | Year | Institution | Email |
|---|---|:---:|---|---|
| **Ashwath Raj** | **Team Lead** | <img src="assets/branding/year-2.svg" width="22" alt="Year 2"> | <img src="https://img.shields.io/badge/SRM_University--AP-B32025?style=flat-square" alt="SRM University-AP"> | [ashwathraj2007@gmail.com](mailto:ashwathraj2007@gmail.com) |
| **Bhamidimarry Venkata Shaileesh** | Team Member | <img src="assets/branding/year-1.svg" width="22" alt="Year 1"> | <img src="https://img.shields.io/badge/VIT_University_AP-0057B8?style=flat-square" alt="VIT University AP"> | [bvshailesh7@gmail.com](mailto:bvshailesh7@gmail.com) |
| **Jammu Venkata Satyam (JVS)** | Team Member | <img src="assets/branding/year-1.svg" width="22" alt="Year 1"> | <img src="https://img.shields.io/badge/VIT_University_AP-0057B8?style=flat-square" alt="VIT University AP"> | [jammuabhi957@gmail.com](mailto:jammuabhi957@gmail.com) |
| **Pagoti Kalyan Vivek** | Team Member | <img src="assets/branding/year-2.svg" width="22" alt="Year 2"> | <img src="https://img.shields.io/badge/VIT_University_AP-0057B8?style=flat-square" alt="VIT University AP"> | [kalyanvivekpagoti@gmail.com](mailto:kalyanvivekpagoti@gmail.com) |

<sub>Roster status in the supplied screenshot: 4 confirmed members out of a 2–6 member team. Two teammate display names are shown with ellipses because the screenshot truncates them; their full registered names should replace these shortened labels when confirmed.</sub>

<p align="center">
  <sub>Built by Team Coughing Baby · SRM University-AP × VIT University AP</sub>
</p>

## Decision-variable interpretation

The organizer clarified that each `x_i` is a binary asset-selection indicator (`x_i ∈ {0,1}`), with exactly `k=2` of the four assets selected. This is a discrete selection QUBO, not a continuous-weight allocation model.


## Supplementary experiments

The notebook preserves the required Master Guide reference A/B × ideal/noisy comparison. It additionally runs a separately labelled topology experiment using PACA-5 (a K4 portfolio core plus two peripheral links) and PACA-9 (a K4 portfolio core plus a five-node peripheral ring). They preserve the 5- and 9-qubit budgets but intentionally change edge counts and connectivity. Ten-seed noisy robustness results, exact q sensitivity, and exact cardinality-penalty sensitivity are exported under `results/tables/`; figures are exported under `results/figures/`. These studies do not replace the required baseline.


## AI assistance disclosure

Generative AI tools assisted with code drafting/review, debugging, and documentation organization for this project. The participant remains responsible for understanding and verifying all methods, assumptions, and results. This disclosure should be checked against the Hackathon & Competitions Cell's official AI-use policy.
