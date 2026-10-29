import json
from pathlib import Path
from collections import deque

ROOT=Path(__file__).resolve().parents[1]

def test_processor_d_structural_constraints():
    p=json.loads((ROOT/'processors/processor_D.json').read_text())
    n=p['num_qubits']; edges=[tuple(e) for e in p['edges']]
    assert 4 <= n <= 12
    assert set(p['basis_gates'])=={'rz','sx','x','cx'}
    assert len(set(tuple(sorted(e)) for e in edges))==len(edges)
    adj={i:set() for i in range(n)}
    for a,b in edges:
        assert 0<=a<n and 0<=b<n and a!=b
        adj[a].add(b);adj[b].add(a)
    assert max(map(len,adj.values()))<=4
    seen={0};todo=deque([0])
    while todo:
        u=todo.popleft()
        for v in adj[u]:
            if v not in seen:seen.add(v);todo.append(v)
    assert len(seen)==n
    assert p['problem_statement']=='PS-O2'
    assert p['noise']['p1']>=0.001 and p['noise']['p2']>=0.005 and p['noise']['p_readout']>=0.01
