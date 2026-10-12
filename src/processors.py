"""Processor topology validation and Master Guide synthetic noise model."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

REFERENCE_EDGES = {
    "Processor A": {(0,1),(1,2),(1,3),(3,4)},
    "Processor B": {(0,1),(1,2),(1,6),(2,3),(2,6),(2,5),(3,4),(4,5),(5,6),(6,7),(6,8),(0,8)},
}

def load_processor(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        item = json.load(f)
    n = int(item["num_qubits"])
    edges = {tuple(sorted(map(int, edge))) for edge in item["coupling_edges_undirected"]}
    if len(edges) != len(item["coupling_edges_undirected"]):
        raise ValueError(f"{path}: duplicate coupling edge")
    if any(u < 0 or v >= n or u == v for u, v in edges):
        raise ValueError(f"{path}: edge outside {n}-qubit graph")
    if item["name"] == "Processor A" and n != 5:
        raise ValueError("Processor A must contain 5 qubits")
    if item["name"] == "Processor B" and n != 9:
        raise ValueError("Processor B must contain 9 qubits")
    item["topology_type"] = "reference_architecture"
    item["is_reference_graph"] = edges == REFERENCE_EDGES[item["name"]]
    return item

def build_synthetic_noise_model() -> NoiseModel:
    """Master Guide rates: 1q depolarizing .001, CX depolarizing .005, readout .01."""
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["rz", "sx", "x"])
    model.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cx"])
    readout = ReadoutError([[0.99, 0.01], [0.01, 0.99]])
    model.add_all_qubit_readout_error(readout)
    return model
