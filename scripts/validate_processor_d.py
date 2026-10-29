#!/usr/bin/env python3
"""Structural preflight for Processor D; official QFF validator remains authoritative."""
from __future__ import annotations
import json, sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'processors/processor_D.json'
p = json.loads(path.read_text(encoding='utf-8'))
errors=[]
n=p.get('num_qubits')
if not isinstance(n,int) or not 4 <= n <= 12:
    errors.append('num_qubits must be an integer between 4 and 12 for PS-O2')
if set(p.get('basis_gates',[])) != {'rz','sx','x','cx'}:
    errors.append('basis_gates must be exactly rz, sx, x, cx')
edges=[]; seen=set(); degree={i:0 for i in range(n if isinstance(n,int) and n>0 else 0)}
for edge in p.get('edges',[]):
    if len(edge)!=2:
        errors.append(f'invalid edge shape: {edge}'); continue
    a,b=map(int,edge)
    if a==b or a<0 or b<0 or a>=n or b>=n:
        errors.append(f'edge endpoint out of range or self-loop: {edge}'); continue
    e=tuple(sorted((a,b)))
    if e in seen: errors.append(f'duplicate undirected edge: {e}'); continue
    seen.add(e); edges.append(e); degree[a]+=1; degree[b]+=1
if degree and max(degree.values())>4: errors.append(f'max degree is {max(degree.values())}; must be <= 4')
adj={i:set() for i in degree}
for a,b in edges: adj[a].add(b); adj[b].add(a)
if adj:
    seen_nodes={0}; q=deque([0])
    while q:
        for v in adj[q.popleft()]:
            if v not in seen_nodes: seen_nodes.add(v); q.append(v)
    if len(seen_nodes)!=n: errors.append(f'graph disconnected: reached {len(seen_nodes)}/{n} nodes')
noise=p.get('noise',{})
for key, floor in [('p1',0.001),('p2',0.005),('p_readout',0.01)]:
    if float(noise.get(key,floor)) < floor: errors.append(f'noise.{key} is below official floor {floor}')
if errors:
    print('Processor D structural preflight: FAIL')
    for e in errors: print(' -', e)
    raise SystemExit(1)
print('Processor D structural preflight: PASS')
print(f"Qubits: {n}; undirected edges: {len(edges)}; max degree: {max(degree.values())}; connected: yes")
print('K4 core on qubits 0-3:', all(tuple(sorted(e)) in seen for e in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]))
print('Note: this structural preflight is not a substitute for qff_phase2.validate_processor_d().')
