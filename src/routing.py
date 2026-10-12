"""QFF Master Guide controlled A/B compilation settings."""
from __future__ import annotations
from typing import Any
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

OPTIMIZATION_LEVEL = 1
TRANSPILER_SEED = 42
SHOTS = 4096
BASIS_GATES = ["rz", "sx", "x", "cx"]

def coupling_map_from_processor(processor: dict[str, Any]) -> CouplingMap:
    directed = []
    for u, v in processor["coupling_edges_undirected"]:
        directed.extend([(int(u), int(v)), (int(v), int(u))])
    cmap = CouplingMap(couplinglist=directed)
    if cmap.size() != int(processor["num_qubits"]):
        raise ValueError(f"Invalid coupling map size for {processor['name']}")
    return cmap

def compile_circuit(circuit: QuantumCircuit, processor: dict[str, Any], *,
                    layout_method: str = "sabre", routing_method: str = "sabre",
                    optimization_level: int = OPTIMIZATION_LEVEL,
                    seed: int = TRANSPILER_SEED, basis_gates: list[str] | None = None) -> QuantumCircuit:
    return transpile(
        circuit,
        coupling_map=coupling_map_from_processor(processor),
        basis_gates=list(basis_gates or processor.get("basis_gates", BASIS_GATES)),
        layout_method=layout_method,
        routing_method=routing_method,
        optimization_level=int(optimization_level),
        seed_transpiler=int(seed),
    )

def swap_diagnostic(circuit: QuantumCircuit, processor: dict[str, Any]) -> int:
    """Separate route diagnostic; preserve SWAPs so they can be counted explicitly."""
    diagnostic_basis = list(processor.get("basis_gates", BASIS_GATES))
    if "swap" not in diagnostic_basis:
        diagnostic_basis.append("swap")
    routed = compile_circuit(circuit.remove_final_measurements(inplace=False), processor,
                             basis_gates=diagnostic_basis)
    return int(routed.count_ops().get("swap", 0))
