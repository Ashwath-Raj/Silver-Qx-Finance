# Phase 2 readiness — historical checkpoint (superseded)

> **Archive note.** This document records an earlier preparation checkpoint and is retained in `Phase One/` for historical traceability. It is not the current status of the active Phase 2 submission.

## Current Phase 2 project

The active Phase 2 project is at the repository root, not inside `Phase One/`.

- [Current README](../README.md)
- [Current technical report](../report.md)
- [Finalization status](../PROOF_OF_WORK_STATUS.md)
- [Processor D1 definition](../processors/processor_D.json)
- [Official result table](../results/tables/results.csv)
- [Bell verification table](../results/tables/bell.csv)
- [Processor D penalty sweep](../results/tables/processor_d_lambda_sweep.csv)

The active root project has locally generated A/B/D ideal/noisy results, the six-value D penalty sweep, adjacent/farthest Bell experiments, and a 10-test suite. Processor D1 is the selected six-qubit K4-tail architecture.

## Reproducibility status

A successful local run is recorded in the root status file. **Clean-clone reproducibility is not considered verified until the current Phase 2 GitHub Actions workflow completes green on the final commit.** The release-hardening patch updates the active workflow to execute the submitted notebook, validate result semantics and cross-artifact consistency, and check that the Processor D plotting script handles all six D1 qubits.

This historical note does not alter or supersede the Phase 1 benchmark data. Phase 2 values come only from the locked `data/instances.json` and the organizer's unchanged `qff_phase2.py`.
