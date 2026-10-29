#!/usr/bin/env python3
"""Render a labelled Processor D graph for mentor discussion and report."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'processors/processor_D.json').read_text())
G=nx.Graph();G.add_nodes_from(range(p['num_qubits']));G.add_edges_from([tuple(e) for e in p['edges']])
pos={0:(0.0,0.0), 1:(1.0,1.8), 2:(2.0,0.0), 3:(1.0,0.65), 4:(1.0,-1.2)}
fig,ax=plt.subplots(figsize=(7.6,4.7))
core=[0,1,2,3]
nx.draw_networkx_edges(G,pos,ax=ax,width=2,edge_color='#4f6f8f')
nx.draw_networkx_nodes(G,pos,nodelist=core,node_size=1500,node_color='#dcecf7',edgecolors='#264b69',linewidths=1.8,ax=ax)
nx.draw_networkx_nodes(G,pos,nodelist=[4],node_size=1500,node_color='#f7e6cf',edgecolors='#8f5821',linewidths=1.8,ax=ax)
nx.draw_networkx_labels(G,pos,labels={i:(f'q{i}\nasset {i}' if i<4 else 'q4\nauxiliary') for i in G.nodes},font_size=9,font_weight='bold',ax=ax)
ax.set_title('Candidate Processor D — K4 asset core + auxiliary physical node')
ax.text(1.0,-1.85,'5 qubits  •  8 edges  •  max degree 4  •  connected',ha='center',fontsize=10)
ax.axis('off');fig.tight_layout()
fig.savefig(ROOT/'results/figures/processor_D_candidate.png',dpi=180,bbox_inches='tight');plt.close(fig)
print('Wrote results/figures/processor_D_candidate.png')
