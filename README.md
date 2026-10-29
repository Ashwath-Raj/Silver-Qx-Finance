# Silver-Qx-Finance — QFF 2026 Quantum Optimization

**Problem:** PS-O2 — Portfolio Optimization with QAOA
**Team:** Coughing Baby · SRM University-AP × VIT-AP

## Repository layout

This repository is the single canonical project. Historical Phase 1 material belongs under `Phase One/` after local setup; active Phase 2 work belongs at the repository root. Do not create a `Phase Two/` directory.

- `qff_phase2.py`: byte-for-byte copy of the organizer's shared measurement utilities. Keep it unchanged.
- `data/instances.json`: byte-for-byte copy of the locked official multi-problem inputs. Do not edit it.
- `data/instance.json`: derived PS-O2 view for this project's exact classical and ideal statevector prototype; it must stay consistent with the official file.
- `processors/processor_D.json`: candidate custom Processor D; it is not yet an official benchmark result.
- `src/classical_reference.py`: exhaustive classical reference, exact QUBO energy and penalty sensitivity.
- `src/qaoa_statevector.py`: a NumPy ideal-statevector p=1 prototype with seeded COBYLA initializations. It does not replace official Qiskit/Aer benchmark runs.
- `main.ipynb`: reproducible development notebook for the current prototype.
- `results/`: generated artifacts. The absence of official `results.csv` and `bell.csv` is intentional until those experiments have actually run.
- `resources/official_docs/`: organizer problem statement, challenge kit, and judging rubric.
- `resources/phase2_starterpack/`: copies of the organizer's starter instructions and requirements.
- `resources/phase1_resources/`: preserved contents from the former `Project phase 1/Resources` folder.
- `resources/organizer_materials/`: a preserved copy of the former `Master Project/Resources` tree, separate from Phase 1 historical resources.

## Locked PS-O2 instance

The official inputs are `mu = [5, 3, 4, 2]`, `q = 0.5`, `k = 2`, with the risk matrix and required `lambda` sweep taken from `data/instances.json`. The required sweep is `[0, 0.5, 1, 2, 5, 10]`. The optimization maximizes

`F(x) = mu^T x - q * x^T Sigma x`, subject to `sum(x) = k`.

The QUBO minimizes `-F(x) + lambda * (sum(x) - k)^2`.

## Setup on Ubuntu

The organizer starter supports Python 3.10–3.12.

```bash
./scripts/setup_environment.sh
source .venv/bin/activate
python scripts/validate_processor_d.py
python scripts/run_classical_reference.py
python scripts/run_qaoa_ideal_prototype.py
python -m pytest -q
```

To smoke-test the unmodified organizer module after Qiskit/Aer are installed:

```bash
python example_usage.py
python scripts/run_official_processor_validation.py
python scripts/run_official_bell.py
```

`example_usage.py` is the organizer's workflow demo; it is not a PS-O2 solver.

## Current scope and limitations

This is an initial reproducible Phase 2 scaffold, not a completed submission. The current tests cover the locked PS-O2 inputs, exact enumeration of 16 states, equivalence between direct and matrix-form QUBO energies, penalty-ground-state feasibility, the ideal-statevector prototype, and Processor D's structural constraints.

The NumPy/SciPy QAOA results are ideal-statevector prototype outputs. They are not Qiskit-transpiled Processor A/B/D results, not noisy Aer results, and not hardware measurements. Official A/B/D benchmark rows, Bell-state verification on adjacent and farthest pairs, the Processor D penalty-sampling sweep, and complete organizer-schema `results/tables/results.csv` and `results/tables/bell.csv` remain to be generated with the provided `qff_phase2.py` utilities.

No quantum-advantage claim is made: this four-variable instance has only 16 bitstrings and is exactly solvable classically.
