#!/usr/bin/env python3
"""Plot exact classical reference and QUBO-ground-state penalty feasibility."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/classical_reference.json').read_text())
valid=r['all_valid_portfolios']
labels=['+'.join(str(i) for i in row['selected_indices']) for row in valid]
values=[row['F'] for row in valid]
fig,ax=plt.subplots(figsize=(8.5,4.8))
ax.bar(labels,values)
ax.set_title('PS-O2 locked instance: exact return-risk objective by valid portfolio')
ax.set_xlabel('Selected asset indices (x0..x3)')
ax.set_ylabel('F(x)')
ax.axhline(r['classical_optimum_F_star'],linestyle='--',linewidth=1,label=f"Exact optimum = {r['classical_optimum_F_star']:.2f}")
ax.legend();ax.grid(axis='y',alpha=.25);fig.tight_layout()
fig.savefig(ROOT/'results/figures/exact_valid_portfolios.png',dpi=160);plt.close(fig)
sweep=r['exact_penalty_sweep']
lam=[row['lambda'] for row in sweep]
valid_ground=[int(row['all_minima_valid']) for row in sweep]
fig,ax=plt.subplots(figsize=(8.5,4.8))
ax.step(lam,valid_ground,where='mid',linewidth=2,marker='o')
ax.set_yticks([0,1],labels=['Invalid minimum','Valid minimum'])
ax.set_xticks(lam)
ax.set_xlabel('Penalty strength lambda')
ax.set_ylabel('Feasibility of exact QUBO ground state')
ax.set_title('Penalty sweep: exact ground-state feasibility (not QAOA sampling)')
ax.grid(alpha=.25);fig.tight_layout()
fig.savefig(ROOT/'results/figures/exact_penalty_sweep.png',dpi=160);plt.close(fig)
print('Wrote results/figures/exact_valid_portfolios.png and exact_penalty_sweep.png')
