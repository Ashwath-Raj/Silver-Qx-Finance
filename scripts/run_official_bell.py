#!/usr/bin/env python3
"""Official Processor D validation and Bell tests using unmodified qff_phase2.py.

Requires Qiskit and Qiskit Aer from requirements.txt. This script is ready for
local execution; this build environment did not have Qiskit installed, so no
Bell output is claimed unless this script has actually been run successfully.
"""
from __future__ import annotations
from pathlib import Path
import csv, json, sys
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qff_phase2 import load_processor, validate_processor_d, bell_experiment, SHOTS

D=load_processor(ROOT/'processors/processor_D.json')
errors=validate_processor_d(D,required_qubits=4)
if errors:
    raise SystemExit('Official Processor D validation failed:\n'+'\n'.join(errors))
print('Official qff_phase2.validate_processor_d: PASS')
G=nx.Graph();G.add_nodes_from(range(D['num_qubits']));G.add_edges_from(D['edges'])
edge=tuple(sorted(D['edges'][0]))
adjacent=(int(edge[0]),int(edge[1]))
dists=dict(nx.all_pairs_shortest_path_length(G))
pairs=[(i,j) for i in range(D['num_qubits']) for j in range(i+1,D['num_qubits'])]
max_distance=max(dists[i][j] for i,j in pairs)
farthest=next((i,j) for i,j in pairs if dists[i][j]==max_distance)
rows=[]
for name,pair in [('adjacent',adjacent),('farthest',farthest)]:
    for noisy in (False,True):
        r=bell_experiment(D,physical_pair=pair,noisy=noisy,shots=SHOTS)
        row={'pair_type':name,'qubit_0':pair[0],'qubit_1':pair[1],**r}
        rows.append(row)
        print(f"{name} pair={pair} distance={r['pair_distance']} noisy={noisy} "
              f"XX={r['XX']:.4f} YY={r['YY']:.4f} ZZ={r['ZZ']:.4f} "
              f"F={r['fidelity']:.4f} +/- {r['fidelity_se']:.4f}")
out=ROOT/'results/tables';out.mkdir(parents=True,exist_ok=True)
fields=['pair_type','qubit_0','qubit_1','pair','pair_distance','noisy','shots','cx',
        'XX','XX_se','YY','YY_se','ZZ','ZZ_se','fidelity','fidelity_se']
with (out/'bell.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for row in rows:
        writer.writerow({k:row.get(k,'') for k in fields})
print(f'Wrote {out / "bell.csv"}')
