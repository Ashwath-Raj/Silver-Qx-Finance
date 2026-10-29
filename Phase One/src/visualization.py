"""Coupling graph plot helper."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

def plot_topology(processor: dict, output: str | Path) -> None:
    graph=nx.Graph(); graph.add_nodes_from(range(int(processor["num_qubits"]))); graph.add_edges_from(processor["coupling_edges_undirected"])
    pos=nx.spring_layout(graph,seed=42); fig,ax=plt.subplots(figsize=(5,4)); nx.draw_networkx(graph,pos,ax=ax,node_size=500,font_size=9); ax.set_title(f"{processor['name']} ({processor['num_qubits']} qubits)"); ax.axis("off"); fig.tight_layout(); fig.savefig(output,dpi=180); plt.close(fig)
