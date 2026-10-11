"""Small plotting utilities for reports and notebooks."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

def plot_processor_topologies(processors: list[dict[str, Any]], output: str | Path) -> None:
    fig, axes = plt.subplots(1, len(processors), figsize=(6 * len(processors), 4.5))
    if len(processors) == 1:
        axes = [axes]
    for ax, processor in zip(axes, processors):
        graph = nx.Graph()
        graph.add_nodes_from(range(int(processor["num_qubits"])))
        graph.add_edges_from(processor["coupling_edges_undirected"])
        pos = nx.spring_layout(graph, seed=17)
        nx.draw_networkx(graph, pos=pos, ax=ax, node_size=620, font_size=9, width=1.7)
        ax.set_title(f"{processor['name']} — {processor['num_qubits']} qubits")
        ax.axis("off")
    fig.tight_layout()
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)
