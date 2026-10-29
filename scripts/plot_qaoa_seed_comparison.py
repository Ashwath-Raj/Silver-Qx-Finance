#!/usr/bin/env python3
"""Plot exact statevector and 4096-draw P_opt estimates across initial seeds."""
from pathlib import Path
import csv
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'results/tables/qaoa_ideal_statevector_prototype.csv'
with path.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
seeds=[int(r['seed']) for r in rows]
exact=[float(r['p_opt_ideal_statevector']) for r in rows]
sampled=[float(r['p_opt_sampled_4096']) for r in rows]
fig,ax=plt.subplots(figsize=(8.2,4.8))
x=range(len(seeds));width=.36
ax.bar([i-width/2 for i in x],exact,width,label='Exact statevector P(opt)')
ax.bar([i+width/2 for i in x],sampled,width,label='4096-draw estimate')
ax.set_xticks(list(x),[str(s) for s in seeds]);ax.set_ylim(0,max(max(exact),max(sampled))*1.2)
ax.set_xlabel('Initial-angle seed');ax.set_ylabel('Optimal-portfolio probability')
ax.set_title('p=1 QAOA prototype: sensitivity to initial angles')
ax.legend();ax.grid(axis='y',alpha=.25);fig.tight_layout()
fig.savefig(ROOT/'results/figures/qaoa_seed_comparison.png',dpi=170);plt.close(fig)
print('Wrote results/figures/qaoa_seed_comparison.png')
