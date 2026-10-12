"""p=1 QAOA and controlled Processor A/B sampling for Master Guide PS-O2."""
from __future__ import annotations
from typing import Any
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from .portfolio_model import bitvector_from_int, enumerate_solutions, full_cost, qubo_coefficients, ising_coefficients, utility
from .routing import compile_circuit, swap_diagnostic, SHOTS, TRANSPILER_SEED, OPTIMIZATION_LEVEL
from .metrics import circuit_metrics

def prepare_cost_model(instance: dict[str, Any]) -> dict[str, Any]:
    mu=np.asarray(instance["expected_returns"],float); sigma=np.asarray(instance["risk_matrix"],float)
    q=float(instance["q"]); k=int(instance["selected_assets_k"]); a=float(instance["cardinality_penalty_A"])
    linear,pair,c=qubo_coefficients(mu,sigma,q,k,a)
    h,j,ising_c=ising_coefficients(linear,pair,c)
    scale=max(float(np.max(np.abs(h))),max((abs(v) for v in j.values()),default=0.0),1e-12)
    return {"linear":linear,"pair":pair,"qubo_constant":c,"h":h,"j":j,
            "ising_constant":ising_c,"phase_scale":scale}

def build_qaoa_circuit(gamma: float, beta: float, cost_model: dict[str,Any], measured: bool=False) -> QuantumCircuit:
    n=len(cost_model["h"]); qc=QuantumCircuit(n,n) if measured else QuantumCircuit(n)
    qc.h(range(n)); scale=float(cost_model["phase_scale"])
    for i,h in enumerate(cost_model["h"]): qc.rz(2*gamma*float(h)/scale,i)
    for (i,j),v in cost_model["j"].items(): qc.rzz(2*gamma*float(v)/scale,i,j)
    for i in range(n): qc.rx(2*beta,i)
    if measured: qc.measure(range(n),range(n))
    return qc

def optimize_qaoa(instance: dict[str,Any], restarts: int=6, maxiter: int=300, seed: int=42) -> dict[str,Any]:
    model=prepare_cost_model(instance); mu=np.asarray(instance["expected_returns"],float); sigma=np.asarray(instance["risk_matrix"],float)
    q=float(instance["q"]); k=int(instance["selected_assets_k"]); a=float(instance["cardinality_penalty_A"]); n=len(mu)
    costs=np.asarray([full_cost(bitvector_from_int(i,n),mu,sigma,q,k,a) for i in range(2**n)],float)
    rng=np.random.default_rng(seed); runs=[]
    for r in range(max(1,int(restarts))):
        x0=np.asarray([0.7,0.4]) if r==0 else np.asarray([rng.uniform(0,2*np.pi),rng.uniform(0,np.pi)])
        def objective(params):
            circuit=build_qaoa_circuit(float(params[0]),float(params[1]),model)
            probs=Statevector.from_instruction(circuit).probabilities()
            return float(np.dot(probs,costs)/model["phase_scale"])
        opt=minimize(objective,x0,method="Nelder-Mead",bounds=[(0,2*np.pi),(0,np.pi)],
                     options={"maxiter":int(maxiter),"xatol":1e-4,"fatol":1e-5})
        runs.append({"restart":r,"gamma":float(opt.x[0]),"beta":float(opt.x[1]),
                     "expected_scaled_cost":float(opt.fun),"success":bool(opt.success),
                     "iterations":int(getattr(opt,"nit",-1)),"message":str(opt.message)})
    best=min(runs,key=lambda x:x["expected_scaled_cost"])
    return {"gamma":best["gamma"],"beta":best["beta"],"best_restart":best["restart"],
            "best_expected_scaled_cost":best["expected_scaled_cost"],"restarts":runs,"cost_model":model}

def sample_processor(instance: dict[str,Any], params: dict[str,Any], processor: dict[str,Any],
                     mode: str="ideal", noise_model=None, shots: int=SHOTS) -> dict[str,Any]:
    logical=build_qaoa_circuit(params["gamma"],params["beta"],params["cost_model"],measured=True)
    swap_count=swap_diagnostic(logical,processor)
    compiled=compile_circuit(logical,processor)
    simulator=AerSimulator(noise_model=noise_model) if mode=="noisy" else AerSimulator()
    result=simulator.run(compiled,shots=int(shots),seed_simulator=TRANSPILER_SEED).result()
    counts=result.get_counts(compiled); total=sum(counts.values())
    mu=np.asarray(instance["expected_returns"],float); sigma=np.asarray(instance["risk_matrix"],float)
    q=float(instance["q"]); k=int(instance["selected_assets_k"]); n=len(mu)
    sols=enumerate_solutions(instance); optimum=max((s for s in sols if s["feasible"]),key=lambda s:s["utility"])
    valid=0; optimal=0; util_all=0.; util_valid=0.; best=None; distribution=[]
    for key,count in counts.items():
        bits=key.replace(" ","")[-n:]
        x=np.asarray([int(bits[-1-i]) for i in range(n)],int)
        ok=int(x.sum())==k; u=utility(x,mu,sigma,q); prob=count/total
        util_all+=prob*u
        row={"bitstring":bits,"bits":x.tolist(),"count":int(count),"probability":float(prob),"valid":bool(ok),"utility":float(u)}
        distribution.append(row)
        if ok:
            valid+=count; util_valid+=count*u
            cand={**row,"selected_assets":[instance["assets"][i] for i,b in enumerate(x) if b]}
            if best is None or u>best["utility"]: best=cand
            if bits==optimum["bitstring"]: optimal+=count
    exact=float(optimum["utility"]); bestu=None if best is None else float(best["utility"])
    ratio=(bestu/exact) if bestu is not None and exact>1e-12 and bestu>=0 else None
    return {"processor":processor["name"],"mode":mode,"processor_qubits":int(processor["num_qubits"]),
            **circuit_metrics(compiled),"shots":int(shots),"layout_method":"sabre","routing_method":"sabre",
            "optimization_level":OPTIMIZATION_LEVEL,"seed_transpiler":TRANSPILER_SEED,
            "swap_count_diagnostic":int(swap_count),"valid_portfolio_probability":valid/total,
            "optimal_portfolio_probability":optimal/total,"sampled_expected_utility_all_outcomes":float(util_all),
            "sampled_expected_utility_given_valid":float(util_valid/valid) if valid else None,
            "exact_optimal_utility":exact,"best_sampled_valid_utility":bestu,
            "optimality_gap":None if bestu is None else exact-bestu,"best_sampled_objective_ratio":ratio,
            "optimal_portfolio":optimum["selected_assets"],"best_sampled_valid":best,
            "counts":{str(k):int(v) for k,v in counts.items()},"sampled_distribution":distribution,
            "transpiled_circuit":compiled}
