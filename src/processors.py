"""Processor topology loaders and validators for the QFF A/B benchmark."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

EXPECTED_EDGES = {
    "Processor A": {(0, 1), (1, 2), (1, 3), (3, 4)},
    "Processor B": {(0, 1), (1, 2), (1, 6), (2, 3), (2, 6), (2, 5),
                     (3, 4), (4, 5), (5, 6), (6, 7), (6, 8), (0, 8)},
}

def load_processor(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        item = json.load(stream)
    n = int(item["num_qubits"])
    edges = {tuple(sorted(map(int, edge))) for edge in item["coupling_edges_undirected"]}
    if len(edges) != len(item["coupling_edges_undirected"]):
        raise ValueError(f"{path}: duplicate coupling edges")
    if any(u < 0 or v >= n or u == v for u, v in edges):
        raise ValueError(f"{path}: invalid edge for {n} qubits")
    expected = EXPECTED_EDGES.get(item["name"])
    if expected is not None and edges != expected:
        raise ValueError(f"{path}: topology differs from the documented {item['name']} map")
    return item
