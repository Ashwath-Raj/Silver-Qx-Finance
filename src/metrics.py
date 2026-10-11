"""Hardware-aware circuit metric extraction."""
from __future__ import annotations
from typing import Any
from qiskit import QuantumCircuit

def circuit_metrics(circuit: QuantumCircuit) -> dict[str, Any]:
    ops = circuit.count_ops()
    physical_qubits_touched = {
        circuit.find_bit(qubit).index
        for instruction in circuit.data
        for qubit in instruction.qubits
    }
    return {
        "num_qubits": int(circuit.num_qubits),
        "physical_qubits_touched": len(physical_qubits_touched),
        "depth": int(circuit.depth()),
        "cx_count": int(ops.get("cx", 0)),
        "swap_count": int(ops.get("swap", 0)),
        "operation_counts": {str(k): int(v) for k, v in ops.items()},
    }
