#!/usr/bin/env python3
"""Run five seeded ideal-statevector p=1 QAOA prototypes for PS-O2."""
from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.classical_reference import load_instance
from src.qaoa_statevector import optimize_restarts
inst=load_instance(ROOT/'data/instance.json')
results=optimize_restarts(inst,penalty=2.0,seeds=(0,1,2,3,4),maxiter=400)
for row in results:
    print(f"seed={row['seed']} E={row['expected_qubo_energy']:.6f} P(valid)={row['valid_probability_ideal_statevector']:.4f} P(opt)={row['p_opt_ideal_statevector']:.4f} sampled_valid={row['valid_frequency_sampled_4096']:.4f} sampled_Popt={row['p_opt_sampled_4096']:.4f} gamma={row['gamma']:.5f} beta={row['beta']:.5f} portfolio={row['selected_valid_bitstring_sampled_x0_to_x3']}")
out=ROOT/'results/tables';out.mkdir(parents=True,exist_ok=True)
# Separate optimizer summaries from full statevector arrays for portable CSV.
with (out/'qaoa_ideal_statevector_prototype.csv').open('w',newline='',encoding='utf-8') as f:
    fields=[k for k in results[0] if k!='statevector_probabilities' and k!='optimizer_message']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for row in results:w.writerow({k:row[k] for k in fields})
# Choose lowest expected energy among all seeds; this is the best ideal-statevector run.
best=min(results,key=lambda r:r['expected_qubo_energy'])
(ROOT/'results/qaoa_ideal_statevector_prototype.json').write_text(json.dumps({'scope':'ideal statevector prototype only; not official compiled/noisy benchmark','best':best,'all_seeds':results},indent=2)+'\n')
print('Wrote results/tables/qaoa_ideal_statevector_prototype.csv and results/qaoa_ideal_statevector_prototype.json')
print('NOTE: no Qiskit transpilation, noisy Aer simulation, or Processor A/B/D resource metric was performed by this prototype.')
