#!/usr/bin/env python3
"""Generate exact PS-O2 classical-reference, QUBO and penalty-sweep artifacts."""
from __future__ import annotations
import csv, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.classical_reference import load_instance, enumerate_reference

instance=load_instance(ROOT/'data/instance.json')
result=enumerate_reference(instance)
out=ROOT/'results/tables'; out.mkdir(parents=True,exist_ok=True)
(ROOT/'results/classical_reference.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
with (out/'classical_solutions.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['bitstring_x0_to_xn','selected_indices','selected_count','valid','F']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for row in result['all_states']:
        row=dict(row); row['selected_indices']=' '.join(map(str,row['selected_indices']))
        w.writerow({k:row[k] for k in fields})
with (out/'exact_penalty_sweep.csv').open('w',newline='',encoding='utf-8') as f:
    rows=result['exact_penalty_sweep']; fields=list(rows[0])
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for row in rows:
        row=dict(row); row['minimizing_bitstrings_x0_to_xn']=';'.join(row['minimizing_bitstrings_x0_to_xn']); row['minimum_cardinality_values']=';'.join(map(str,row['minimum_cardinality_values'])); w.writerow(row)
print('PS-O2 exact classical reference generated')
print('Valid portfolios:',result['valid_portfolio_count'],'of',result['state_count'])
print('Classical optimum F*:',result['classical_optimum_F_star'])
print('Optimal bitstrings x0..x3:',[r['bitstring_x0_to_xn'] for r in result['optimal_portfolios']])
print('Uniform baseline:',json.dumps(result['uniform_random_baseline'],sort_keys=True))
print('Penalty sweep:')
for row in result['exact_penalty_sweep']:
    print(f"  lambda={row['lambda']:>4}: minimum valid={row['all_minima_valid']}; minimizing={row['minimizing_bitstrings_x0_to_xn']}; cardinalities={row['minimum_cardinality_values']}")
print('Artifacts: results/classical_reference.json, results/tables/classical_solutions.csv, results/tables/exact_penalty_sweep.csv')
print('SCOPE: this script is the exact classical reference only. The separate p=1 QAOA prototype is in scripts/run_qaoa_ideal_prototype.py; the required noisy/ideal processor benchmark is still pending.')
