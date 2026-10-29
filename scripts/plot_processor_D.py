#!/usr/bin/env python3
"""Render the selected Processor D graph without assuming a fixed qubit count.

This script intentionally derives every node label and position from the JSON. The
former five-position map raised KeyError for D1's sixth physical qubit (q5).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
processor_path = ROOT / "processors" / "processor_D.json"
processor = json.loads(processor_path.read_text(encoding="utf-8"))
n_qubits = int(processor["num_qubits"])
edges = [tuple(map(int, edge)) for edge in processor["edges"]]
G = nx.Graph()
G.add_nodes_from(range(n_qubits))
G.add_edges_from(edges)

# Keep a purpose-built D1 layout for readability. Other valid processor graphs use
# a deterministic spring layout and therefore never index an incomplete position map.
D1_EDGES = {
    (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (2, 3), (4, 5)
}
normalized_edges = {tuple(sorted(edge)) for edge in edges}
if n_qubits == 6 and normalized_edges == D1_EDGES:
    pos = {
        0: (0.0, 0.0), 1: (1.1, 1.15), 2: (2.2, 0.0), 3: (1.1, -1.15),
        4: (-1.1, 0.0), 5: (-2.2, -0.72),
    }
else:
    pos = nx.spring_layout(G, seed=42, k=max(0.8, 1.7 / max(n_qubits, 1)))

core = [q for q in G.nodes if q < min(4, n_qubits)]
auxiliary = [q for q in G.nodes if q not in core]
labels = {
    q: (f"q{q}\nasset {q}" if q < 4 else f"q{q}\nauxiliary")
    for q in G.nodes
}
max_degree = max(dict(G.degree()).values(), default=0)
connected = (n_qubits > 0 and nx.is_connected(G))

fig, ax = plt.subplots(figsize=(8.4, 5.4))
nx.draw_networkx_edges(G, pos, ax=ax, width=2.1, edge_color="#4F6F8F")
if core:
    nx.draw_networkx_nodes(
        G, pos, nodelist=core, node_size=1450, node_color="#DCECF7",
        edgecolors="#264B69", linewidths=1.8, ax=ax,
    )
if auxiliary:
    nx.draw_networkx_nodes(
        G, pos, nodelist=auxiliary, node_size=1450, node_color="#F7E6CF",
        edgecolors="#8F5821", linewidths=1.8, ax=ax,
    )
nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight="bold", ax=ax)
ax.set_title("Selected Processor D1 — K4 asset core + two-edge tail", fontsize=13, fontweight="bold")
status = "connected" if connected else "disconnected"
ax.text(
    0.5, -0.09,
    f"{n_qubits} physical qubits  •  {G.number_of_edges()} couplers  •  max degree {max_degree}  •  {status}",
    transform=ax.transAxes, ha="center", fontsize=9.5,
)
ax.axis("off")
fig.tight_layout()
output = ROOT / "results" / "figures" / "processor_d_topology.png"
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output, dpi=180, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {output.relative_to(ROOT)} ({n_qubits} qubits, {G.number_of_edges()} couplers)")
