"""Processor topology validation and Master Guide synthetic noise model."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
import networkx as nx

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


# Supplementary participant-designed topologies. These never replace the Master Guide
# reference processor JSON files or the required baseline result table.
ALTERNATIVE_TOPOLOGIES = {
    "Processor A": {
        "label": "alternative linear chain",
        "edges": [(0, 1), (1, 2), (2, 3), (3, 4)],
        "rationale": "Same 5 nodes and 4 edges as the reference tree; tests the effect of a chain versus branching connectivity.",
    },
    "Processor B": {
        "label": "alternative balanced ring with chords",
        "edges": [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
            (5, 6), (6, 7), (7, 8), (0, 8),
            (0, 4), (1, 5), (2, 6),
        ],
        "rationale": "Same 9 nodes and 12 edges as the reference graph, with a more balanced degree profile and shorter graph diameter in the structural check.",
    },
}

def topology_metrics(processor: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic graph-structure metrics for a processor configuration."""
    graph = nx.Graph()
    graph.add_nodes_from(range(int(processor["num_qubits"])))
    graph.add_edges_from(tuple(sorted(map(int, edge))) for edge in processor["coupling_edges_undirected"])
    if not nx.is_connected(graph):
        raise ValueError(f"Topology for {processor['name']} must be connected.")
    degrees = [int(graph.degree(node)) for node in range(graph.number_of_nodes())]
    return {
        "num_qubits": int(graph.number_of_nodes()),
        "edge_count": int(graph.number_of_edges()),
        "degree_sequence_by_node": degrees,
        "minimum_degree": min(degrees),
        "maximum_degree": max(degrees),
        "degree_mean": float(sum(degrees) / len(degrees)),
        "degree_std_population": float((sum((degree - sum(degrees) / len(degrees)) ** 2 for degree in degrees) / len(degrees)) ** 0.5),
        "diameter": int(nx.diameter(graph)),
        "average_shortest_path_length": float(nx.average_shortest_path_length(graph)),
        "connected": True,
    }

def make_topology_variant(processor: dict[str, Any], label: str, edges: list[list[int]] | list[tuple[int, int]]) -> dict[str, Any]:
    """Create a validated in-memory alternative without mutating the baseline config."""
    n = int(processor["num_qubits"])
    normalized = sorted({tuple(sorted((int(edge[0]), int(edge[1])))) for edge in edges})
    if len(normalized) != len(edges):
        raise ValueError(f"{label}: duplicate or repeated undirected edges")
    if any(u == v or u < 0 or v >= n for u, v in normalized):
        raise ValueError(f"{label}: edge outside the {n}-qubit topology")
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(normalized)
    if not nx.is_connected(graph):
        raise ValueError(f"{label}: topology must be connected")
    variant = dict(processor)
    variant["name"] = f"{processor['name']} — alternative: {label}"
    variant["coupling_edges_undirected"] = [list(edge) for edge in normalized]
    variant["topology_type"] = "participant_designed_alternative_supplementary"
    variant["is_reference_graph"] = False
    variant["topology_rationale"] = ALTERNATIVE_TOPOLOGIES.get(processor["name"], {}).get("rationale", label)
    return variant
