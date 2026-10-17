# QFF 2026 Phase 2 Readiness

Project: Silver-Qx-Finance
Problem: PS-O2 — Portfolio Optimization with QAOA

## Current scope
This is a Phase 2 preparation scaffold, not a claim of completed Phase 2 work.
The generic processor loader and routing path accept additional processor definitions.
The official Drive directions are linked from the learning workspace, but their
contents have not yet been ingested into this repository. Processor C's exact
specification, custom Processor D constraints, and enhanced PS-O2 rules remain
unintegrated; no official C/D topology or performance is invented.

## Preserve
- Processor A/B definitions and baseline results.
- Portfolio input, QUBO parameters and classical reference.
- Existing notebook, tests, figures and report.
- Phase 1 Git commit: e2b9f25.

## Start gate
Before implementing C/D, confirm:
1. Team shortlisted for Phase 2.
2. Enhanced PS-O2 problem statement received.
3. Official Processor C topology and execution rules received.
4. Processor D design constraints received.
5. Official Phase 2 start confirmed.

## Workflow
1. Run scripts/phase2_preflight.py.
2. Run scripts/phase2_validate.sh.
3. Fill in config/phase2_requirements.template.json from official sources.
4. Implement C/D only after the start gate is satisfied.
5. Benchmark, test, document and package the results.
