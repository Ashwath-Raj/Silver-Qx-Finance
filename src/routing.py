"""Reusable topology-aware transpilation helpers."""
from __future__ import annotations
from typing import Any
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

def coupling_map_from_processor(processor: dict[str, Any]) -> CouplingMap:
    directed = []
    for u, v in processor["coupling_edges_undirected"]:
        directed.extend([(int(u), int(v)), (int(v), int(u))])
    coupling = CouplingMap(couplinglist=directed)
    if coupling.size() != int(processor["num_qubits"]):
        raise ValueError(f"Unexpected qubit count for {processor['name']}")
    return coupling

def compile_circuit(circuit: QuantumCircuit, processor: dict[str, Any], *,
                    layout_method: str = "trivial", routing_method: str = "basic",
                    optimization_level: int = 0, seed: int = 2026) -> QuantumCircuit:
    return transpile(
        circuit,
        coupling_map=coupling_map_from_processor(processor),
        basis_gates=list(processor["basis_gates"]),
        layout_method=layout_method,
        routing_method=routing_method,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )
