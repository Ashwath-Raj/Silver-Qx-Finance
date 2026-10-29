# Proof-of-work status — 29 October 2026

## Completed and reproduced in the current container

- Phase 2 official PS-O2 input copied to `data/instance.json`.
- Organizer starter `qff_phase2.py` copied unchanged. SHA-256 matches the source starter-pack file: `04be4fa610ba60854a2b3b9237891df7e8ade62e2fcd9659076e36e794f077ab`.
- Exact enumeration: 16 bitstrings, six valid portfolios, `F*=4.75`, optimum `x0..x3=1100` (asset indices 0 and 1).
- Direct QUBO energy and symmetric-matrix energy match across all 16 bitstrings, tested automatically.
- Exact penalty ground state is invalid for lambda 0 and 0.5; valid for lambda 1, 2, 5 and 10.
- A custom NumPy statevector p=1 QAOA prototype optimizes from initial-angle seeds 0–4 with COBYLA, and records exact ideal probabilities plus deterministic 4096-draw estimates.
- Candidate Processor D structurally satisfies connectivity, 5–12 qubit capacity, max degree 4, basis declaration and noise floors.
- Six automated tests pass. The Jupyter notebook executes successfully in the current environment.

## Not done / do not overclaim

- The official Processor D validator and Bell experiments have not been run in the current container because Qiskit and Qiskit Aer are not installed here; installation was blocked by package-index DNS/network availability.
- No official Qiskit-transpiled A/B/D resource table has been produced.
- The official noisy Aer runs, final A/B/D comparisons, and Processor D QAOA penalty-sweep sampling are not complete.
- Therefore `results/tables/results.csv` and `results/tables/bell.csv` are intentionally absent rather than populated with invented or placeholder benchmark results.
- This is an intermediate proof-of-work commit, not the complete judged submission.
