"""Circuit metrics for QFF A/B benchmark."""
from __future__ import annotations
from typing import Any
from qiskit import QuantumCircuit

def circuit_metrics(circuit: QuantumCircuit) -> dict[str, Any]:
    ops = circuit.count_ops()
    touched = {circuit.find_bit(q).index for inst in circuit.data for q in inst.qubits}
    return {"compiled_qubits": int(circuit.num_qubits), "physical_qubits_touched": len(touched),
            "depth": int(circuit.depth()), "cx_count": int(ops.get("cx", 0)),
            "swap_count_native": int(ops.get("swap", 0)),
            "operation_counts": {str(k): int(v) for k,v in ops.items()}}
