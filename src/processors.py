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
    """Load and validate any processor JSON; apply fixed size rules only to reference A/B."""
    with Path(path).open("r", encoding="utf-8") as f:
        item = json.load(f)

    if not isinstance(item, dict):
        raise ValueError(f"{path}: processor definition must be a JSON object")

    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{path}: processor name must be a non-empty string")

    try:
        raw_n = item["num_qubits"]
        n = int(raw_n)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{path}: num_qubits must be a positive integer") from exc
    if isinstance(raw_n, bool) or n < 1 or (isinstance(raw_n, float) and not raw_n.is_integer()):
        raise ValueError(f"{path}: num_qubits must be a positive integer")

    raw_edges = item.get("coupling_edges_undirected")
    if not isinstance(raw_edges, list):
        raise ValueError(f"{path}: coupling_edges_undirected must be a list")

    edges: set[tuple[int, int]] = set()
    for index, edge in enumerate(raw_edges):
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise ValueError(f"{path}: coupling edge {index} must contain exactly two qubit indices")
        try:
            raw_u, raw_v = edge
            u, v = int(raw_u), int(raw_v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}: coupling edge {index} contains a non-integer qubit index") from exc
        if (
            isinstance(raw_u, bool) or isinstance(raw_v, bool)
            or (isinstance(raw_u, float) and not raw_u.is_integer())
            or (isinstance(raw_v, float) and not raw_v.is_integer())
        ):
            raise ValueError(f"{path}: coupling edge {index} contains a non-integer qubit index")
        if u < 0 or v < 0 or u >= n or v >= n or u == v:
            raise ValueError(f"{path}: coupling edge {index} is outside the {n}-qubit graph or is a self-loop")
        normalized = tuple(sorted((u, v)))
        if normalized in edges:
            raise ValueError(f"{path}: duplicate coupling edge {normalized}")
        edges.add(normalized)

    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(edges)
    if not nx.is_connected(graph):
        raise ValueError(f"{path}: coupling graph must be connected")

    if name == "Processor A" and n != 5:
        raise ValueError("Processor A must contain 5 qubits")
    if name == "Processor B" and n != 9:
        raise ValueError("Processor B must contain 9 qubits")

    # The official A/B graphs are the only reference maps currently encoded here.
    # New processor names (including a future Processor C) remain unclassified until
    # their official topology and status are supplied; never index REFERENCE_EDGES blindly.
    if name in REFERENCE_EDGES:
        item["topology_type"] = "reference_architecture"
        item["is_reference_graph"] = edges == REFERENCE_EDGES[name]
    else:
        item.setdefault("topology_type", "unclassified_processor")
        item["is_reference_graph"] = False

    return item

def build_synthetic_noise_model() -> NoiseModel:
    """Master Guide rates: 1q depolarizing .001, CX depolarizing .005, readout .01."""
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["rz", "sx", "x"])
    model.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cx"])
    readout = ReadoutError([[0.99, 0.01], [0.01, 0.99]])
    model.add_all_qubit_readout_error(readout)
    return model


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

# PACA-TOPOLOGY-SPECS-BEGIN
# Participant-designed alternatives. These do NOT replace the Master Guide reference JSONs.
PACA_TOPOLOGY_SPECS = {
    "Processor A": {
        "label": "PACA-5 — custom K4 core + two peripheral links",
        "edges": [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3), (0, 4), (2, 4)],
        "rationale": "PACA-5 is a participant-designed 5-qubit supplementary topology. Physical nodes 0–3 form a K4 clique that can support direct pairwise interactions among four logical asset variables when the transpiler maps them to that core; node 4 is a peripheral node linked to nodes 0 and 2. Layout is selected by the configured transpiler, so the core is a design hypothesis rather than a guarantee of better performance. Not an official Master Guide reference graph.",
    },
    "Processor B": {
        "label": "PACA-9 — custom K4 core + five-node peripheral ring",
        "edges": [
            (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),
            (4, 5), (5, 6), (6, 7), (7, 8), (4, 8),
            (0, 4), (1, 5), (2, 6), (3, 7), (0, 8),
        ],
        "rationale": "PACA-9 is a participant-designed 9-qubit supplementary topology. Nodes 0–3 form a K4 clique, nodes 4–8 form a ring, and five links connect the core to the ring. It has 16 edges and deliberately is not edge-count-matched to the 12-edge reference B graph. Layout is selected by the configured transpiler; additional connectivity does not guarantee lower circuit cost or better noisy solution quality. Not an official Master Guide reference graph.",
    },
}
ALTERNATIVE_TOPOLOGIES = PACA_TOPOLOGY_SPECS
# PACA-TOPOLOGY-SPECS-END

# PACA-MAKE-TOPOLOGY-VARIANT-BEGIN
def make_topology_variant(processor, label, edges):
    """Create a validated custom topology in memory; reference configs remain unchanged."""
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
    variant["name"] = f"{processor['name']} — custom supplementary: {label}"
    variant["coupling_edges_undirected"] = [list(edge) for edge in normalized]
    variant["topology_type"] = "participant_designed_custom_supplementary"
    variant["is_reference_graph"] = False
    variant["topology_rationale"] = ALTERNATIVE_TOPOLOGIES.get(processor["name"], {}).get("rationale", label)
    return variant
# PACA-MAKE-TOPOLOGY-VARIANT-END
