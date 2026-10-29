"""Example: how to use qff_phase2.py. Run:  python example_usage.py
This does NOT solve any problem statement - it shows the official measurement workflow."""
import json
from qiskit import QuantumCircuit
from qff_phase2 import (PROCESSOR_A, PROCESSOR_B, load_processor, validate_processor_d,
                        circuit_metrics, transpile_for, simulator, bell_experiment,
                        counts_to_x, SHOTS)

# 1) Your Processor D (copy processor_D_template.json -> processors/processor_D.json and edit)
D = load_processor("processor_D_template.json")
print("Processor D rule check:", validate_processor_d(D, required_qubits=6) or "OK")

# 2) Objective 1 - Bell state on an adjacent physical pair of D, ideal and noisy
for noisy in (False, True):
    r = bell_experiment(D, physical_pair=(0, 1), noisy=noisy)
    print(f"Bell noisy={noisy}: XX={r['XX']:.3f} YY={r['YY']:.3f} ZZ={r['ZZ']:.3f} "
          f"F={r['fidelity']:.4f} +/- {r['fidelity_se']:.4f}")

# 3) Official metrics for ANY circuit (replace with your QAOA circuit)
qc = QuantumCircuit(6)
qc.h(range(6))
for a, b in [(0, 3), (2, 5), (1, 4), (0, 5)]:
    qc.cx(a, b); qc.rz(0.3, b); qc.cx(a, b)
qc.measure_all()
for P in (PROCESSOR_A, PROCESSOR_B, D):
    print(json.dumps(circuit_metrics(qc, P)))

# 4) Run on D with noise and convert keys to x0..x5
t = transpile_for(qc, D)
counts = simulator(noisy=True, processor=D).run(t, shots=SHOTS).result().get_counts()
key = max(counts, key=counts.get)
print("most frequent key", key, "-> x =", counts_to_x(key))
