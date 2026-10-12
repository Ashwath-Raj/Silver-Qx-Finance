#!/usr/bin/env python3
"""Run the QFF Phase 1 Master Guide PS-O2 A/B benchmark."""
from __future__ import annotations
import argparse, csv, json, os, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from qiskit import qasm3
from src.portfolio_model import load_instance, enumerate_solutions, qubo_matrix, validate_qubo_conversion
from src.processors import load_processor, build_synthetic_noise_model
from src.qaoa import optimize_qaoa, sample_processor

ROOT=Path(__file__).resolve().parent; DATA=ROOT/"data/portfolio_instance.json"; PROC=ROOT/"processors"; RESULTS=ROOT/"results"

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f: json.dump(data,f,indent=2,allow_nan=False)

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: return
    fields=list(rows[0].keys())
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n"); w.writeheader()
        for row in rows: w.writerow({k:(json.dumps(v) if isinstance(v,(dict,list)) else v) for k,v in row.items() if k in fields})

def resolve_q(instance):
    q=instance.get("q")
    if q is not None: return float(q),False
    env=os.getenv("QFF_Q")
    if env is not None: q=float(env)
    elif sys.stdin.isatty():
        raw=input("Master Guide does not specify q. Enter a positive participant-selected q [1.0]: ").strip()
        q=1.0 if not raw else float(raw)
    else:
        raise SystemExit("q is unspecified in the Master Guide. Set it transparently in data/portfolio_instance.json or run QFF_Q=1.0 python main.py")
    if q<=0: raise ValueError("q must be positive")
    instance["q"]=q; instance["q_selection_status"]="participant-selected; QFF Master Guide does not state a numerical q"
    write_json(DATA,instance)
    return q,True

def strip_circuit(row):
    row=dict(row); row.pop("transpiled_circuit",None); row.pop("counts",None); row.pop("sampled_distribution",None)
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--q",type=float,default=None,help="positive q; Master Guide does not prescribe a value")
    ap.add_argument("--skip-noisy",action="store_true",help="run ideal baseline only")
    args=ap.parse_args()
    RESULTS.mkdir(exist_ok=True); (RESULTS/"figures").mkdir(parents=True,exist_ok=True); (RESULTS/"tables").mkdir(parents=True,exist_ok=True)
    instance=load_instance(DATA)
    if args.q is not None:
        if args.q<=0: raise ValueError("--q must be positive")
        instance["q"]=float(args.q); instance["q_selection_status"]="participant-selected CLI value; QFF Master Guide does not state q"
        write_json(DATA,instance); q=float(args.q); q_was_prompted=False
    else: q,q_was_prompted=resolve_q(instance)
    instance=load_instance(DATA); validate_qubo_conversion(instance)
    a=float(instance["cardinality_penalty_A"]); q=float(instance["q"])
    print(f"PS-O2 Master Guide inputs loaded: mu={instance['expected_returns']}, k=2, q={q}, A={a}")
    print("NOTE: q is participant-selected because the Master Guide does not assign a value. The report will disclose this.")
    solutions=enumerate_solutions(instance,a); feasible=[s for s in solutions if s["feasible"]]
    optimum=max(feasible,key=lambda s:s["utility"])
    Q,c=qubo_matrix(instance)
    with (RESULTS/"tables/qubo_matrix.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["asset"]+instance["assets"]);
        for i,name in enumerate(instance["assets"]): w.writerow([name]+[float(v) for v in Q[i]])
    write_json(RESULTS/"tables/qubo_matrix.json",{"convention":"C(x)=x.T @ Q @ x + constant","Q":Q.tolist(),"constant":c,"q":q,"penalty_A":a})
    params=optimize_qaoa(instance,restarts=int(instance.get("classical_restarts",6)),maxiter=int(instance.get("optimizer_maxiter",300)),seed=42)
    processors=[load_processor(PROC/"processor_A.json"),load_processor(PROC/"processor_B.json")]
    noise=build_synthetic_noise_model(); rows=[]; full=[]
    for processor in processors:
        for mode in (["ideal"] if args.skip_noisy else ["ideal","noisy"]):
            print(f"Running {processor['name']} / {mode} with SABRE, level 1, seed 42, 4096 shots...")
            row=sample_processor(instance,params,processor,mode=mode,noise_model=noise if mode=="noisy" else None,shots=4096)
            full.append(row); rows.append(strip_circuit(row))
            try:
                (RESULTS/f"compiled_{processor['name'].lower().replace(' ','_')}_{mode}.qasm").write_text(qasm3.dumps(row["transpiled_circuit"]),encoding="utf-8")
            except Exception as exc: print(f"QASM export note: {exc}")
    write_json(RESULTS/"classical_solutions.json",{"solutions":solutions,"exact_optimum":optimum})
    write_json(RESULTS/"qaoa_parameters.json",{"gamma":params["gamma"],"beta":params["beta"],"best_restart":params["best_restart"],"best_expected_scaled_cost":params["best_expected_scaled_cost"],"restarts":params["restarts"],"q":q,"penalty_A":a})
    output_rows=[]
    for row in rows:
        output_rows.append({k:v for k,v in row.items() if k not in ("counts",)})
    write_csv(RESULTS/"processor_comparison.csv",output_rows); write_csv(RESULTS/"tables/processor_comparison.csv",output_rows)
    metadata={"problem_code":"PS-O2","instance_source":"QFF_Phase_1_Master_Guide.pdf page 4 inputs","expected_returns":instance["expected_returns"],"risk_matrix":instance["risk_matrix"],"q":q,"q_status":instance.get("q_selection_status","participant-selected; q is not stated in Master Guide"),"cardinality_k":2,"cardinality_penalty_A":a,"penalty_source_note":instance.get("penalty_source_note"),"shots":4096,"optimization_level":1,"layout_method":"sabre","routing_method":"sabre","seed_transpiler":42,"noise_model":{"one_qubit_depolarizing":0.001,"cx_depolarizing":0.005,"readout_bitflip":0.01},"noise_note":"Master Guide synthetic noise model; ideal and noisy results separated","qaoa_depth_p":1}
    write_json(RESULTS/"run_metadata.json",metadata)
    # Plots: exact objective of all feasible portfolios.
    labels=[" + ".join(s["selected_assets"]) for s in sorted(feasible,key=lambda z:z["utility"],reverse=True)]
    values=[s["utility"] for s in sorted(feasible,key=lambda z:z["utility"],reverse=True)]
    fig,ax=plt.subplots(figsize=(10,5)); ax.bar(range(len(values)),values); ax.set_xticks(range(len(values)),labels,rotation=35,ha="right"); ax.set_ylabel("Unpenalized objective q·return − risk"); ax.set_title("Exact classical feasible portfolios"); ax.grid(axis="y",alpha=.25); fig.tight_layout(); fig.savefig(RESULTS/"figures/classical_portfolio_objectives.png",dpi=180); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    for ax,processor in zip(axes,processors):
        g=nx.Graph(); g.add_nodes_from(range(processor["num_qubits"])); g.add_edges_from(processor["coupling_edges_undirected"]); pos=nx.spring_layout(g,seed=42); nx.draw_networkx(g,pos,ax=ax,node_size=500,font_size=9); ax.set_title(f"{processor['name']} ({processor['num_qubits']} qubits)"); ax.axis("off")
    fig.tight_layout(); fig.savefig(RESULTS/"figures/processor_topologies.png",dpi=180); plt.close(fig)
    for row in full:
        dist=sorted(row["sampled_distribution"],key=lambda z:z["probability"],reverse=True)[:12]; fig,ax=plt.subplots(figsize=(8,4)); ax.bar([x["bitstring"] for x in dist],[x["probability"] for x in dist]); ax.set_title(f"{row['processor']} — {row['mode']} outcome distribution"); ax.set_xlabel("Bitstring (asset 4 … asset 1)"); ax.set_ylabel("Probability"); fig.tight_layout(); fig.savefig(RESULTS/f"figures/qaoa_distribution_{row['processor'].lower().replace(' ','_')}_{row['mode']}.png",dpi=180); plt.close(fig)
    # Report includes source and configuration qualifications.
    lines=["# QFF 2026 Phase 1 — PS-O2 Portfolio Optimization","","## Benchmark provenance","",f"- Inputs: QFF Phase 1 Master Guide, page 4.",f"- Returns μ: `{instance['expected_returns']}`",f"- Risk matrix minimum eigenvalue: `{instance['risk_matrix_min_eigenvalue']:.8f}`",f"- q: `{q}` — participant-selected because the Master Guide's PS-O2 section does not prescribe a numeric value.",f"- Cardinality: exactly 2 assets.",f"- Penalty A: `{a}`. {instance.get('penalty_source_note','Review the penalty convention against the event instructions before submission.')}","- Formulation: minimize `x.T @ Sigma @ x - q * mu.T @ x + A * (sum(x)-2)^2`.","- Reported economic objective: `q * mu.T @ x - x.T @ Sigma @ x`, only on feasible portfolios.","","## Exact classical reference","",f"- Optimal portfolio: {', '.join(optimum['selected_assets'])}",f"- Bitstring (asset 4 … asset 1): `{optimum['bitstring']}`",f"- Best feasible unpenalized objective: `{optimum['utility']:.10f}`","","## Controlled Processor A/B results","","| Processor | Mode | Qubits | Depth | CX | SWAP diagnostic | Valid probability | Optimal probability | Best feasible objective | Ratio | Gap |","|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        ratio="N/A" if r.get("best_sampled_objective_ratio") is None else f"{r['best_sampled_objective_ratio']:.6f}"
        best="N/A" if r.get("best_sampled_valid_utility") is None else f"{r['best_sampled_valid_utility']:.8f}"
        gap="N/A" if r.get("optimality_gap") is None else f"{r['optimality_gap']:.8f}"
        lines.append(f"| {r['processor']} | {r['mode']} | {r['processor_qubits']} | {r['depth']} | {r['cx_count']} | {r['swap_count_diagnostic']} | {r['valid_portfolio_probability']:.4f} | {r['optimal_portfolio_probability']:.4f} | {best} | {ratio} | {gap} |")
    lines += ["","## Compilation protocol","","- QAOA p=1; same logical circuit and optimized angles for both processors.","- Basis gates `{rz, sx, x, cx}`; optimization level 1; SABRE layout/routing; transpiler seed 42; 4096 shots.","- Noise model: one-qubit depolarizing 0.001; CX depolarizing 0.005. The guide only gives a 1% readout error rate, not a confusion matrix; this implementation models it as symmetric 1% bit-flip and records that assumption. Ideal and noisy runs are reported separately.","- SWAP count comes from a separate diagnostic transpilation with SWAP retained; it is not the native-basis circuit's literal SWAP count.","","## Interpretation and limitations","","- Four assets yield only 16 bitstrings and can be solved exactly classically; no quantum advantage is claimed.","- The numeric q is not specified in the Master Guide and was selected for this run; official status requires the organizers' interpretation or documented acceptance.","- Coupling graphs are reference architectures. The included A/B runs use the documented reference edges; any participant-designed topology must be reported separately.","- The synthetic noise results are Aer simulation measurements, not hardware measurements.","","## Reproducibility","","Run `python -m unittest discover -s tests -v`, then `python main.py --q <chosen-positive-q>`. Results are regenerated under `results/`.",""]
    (ROOT/"report.md").write_text("\n".join(lines),encoding="utf-8"); (RESULTS/"report.md").write_text("\n".join(lines),encoding="utf-8")
    print("\nBenchmark complete. Best feasible classical portfolio:", ", ".join(optimum["selected_assets"]))
    print("Results:",RESULTS)
    print("IMPORTANT: q was selected by the participant because the Master Guide does not specify it. Read report.md before treating values as official.")

if __name__=="__main__": main()
