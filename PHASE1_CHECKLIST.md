# Phase 1 execution checklist — O2

## Gate 0: Confirm data and organizer rules
- [ ] Confirm whether the organizer has a fixed 4×4 risk matrix and fixed benchmark parameter values.
- [ ] Confirm official noise parameters and supported processor instructions.
- [ ] Confirm the submission cut-off time/time zone from the official form.
- [ ] Record any official AI-assistance disclosure requirement.

## Gate 1: Core solution
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Replace the synthetic fixture if the organizer supplies authoritative data.
- [ ] Run `python main.py` successfully from a clean venv.
- [ ] Confirm exact classical optimum and p=1 QAOA outputs are feasible / interpreted correctly.

## Gate 2: Required A/B comparison
- [ ] Use identical logical instance, QAOA parameters, shots, basis gates, layout rule and routing rule on A/B.
- [ ] Save CX count, circuit depth, SWAP overhead, valid-portfolio probability and optimal-portfolio probability.
- [ ] Verify processor coupling maps against official Challenge Kit before submission.
- [ ] Explain results with measured evidence; do not infer architecture effects from qubit count alone.

## Gate 3: Submission package
- [ ] `main.py` runs end-to-end.
- [ ] `requirements.txt` is present.
- [ ] Processor files and input provenance are documented.
- [ ] CSV, figures, README and report are present.
- [ ] Official noise results are included only if required and only from authoritative settings.
- [ ] No quantum-advantage claim is made from a four-variable toy instance.
- [ ] Repository URL and required AI-use disclosure are ready for submission.
