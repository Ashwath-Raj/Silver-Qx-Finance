"""PS-O2 mathematical model from the QFF Phase 1 Master Guide."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np

MASTER_GUIDE_MU = [0.12, 0.18, 0.10, 0.22]
MASTER_GUIDE_SIGMA = [
    [0.04, 0.01, 0.02, 0.01],
    [0.01, 0.09, 0.01, 0.03],
    [0.02, 0.01, 0.05, 0.02],
    [0.01, 0.03, 0.02, 0.08],
]

def load_instance(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    assets = data.get("assets")
    mu = np.asarray(data.get("expected_returns"), dtype=float)
    sigma = np.asarray(data.get("risk_matrix"), dtype=float)
    if (not isinstance(assets, list) or len(assets) != 4
            or any(not isinstance(asset, str) or not asset.strip() for asset in assets)
            or len(set(assets)) != 4):
        raise ValueError("PS-O2 requires four unique, non-empty asset names.")
    if mu.shape != (4,) or sigma.shape != (4, 4):
        raise ValueError("PS-O2 inputs must have a 4-element return vector and a 4x4 risk matrix.")
    if not np.all(np.isfinite(mu)) or not np.all(np.isfinite(sigma)):
        raise ValueError("Expected returns and risk matrix must contain only finite numbers.")
    if not np.allclose(sigma, sigma.T, atol=1e-10):
        raise ValueError("Risk matrix must be symmetric.")
    if float(np.linalg.eigvalsh(sigma).min()) < -1e-8:
        raise ValueError("Risk matrix must be positive semidefinite.")
    k = int(data.get("selected_assets_k", 2))
    if k != 2:
        raise ValueError("Master Guide PS-O2 requires k=2.")
    q = data.get("q")
    if q is not None:
        q = float(q)
        if not np.isfinite(q) or q <= 0:
            raise ValueError("q must be finite and positive.")
    if "cardinality_penalty_A" not in data:
        raise ValueError("Set the participant-selected cardinality penalty A explicitly.")
    a = float(data["cardinality_penalty_A"])
    if not np.isfinite(a) or a <= 0:
        raise ValueError("Cardinality penalty A must be finite and positive.")
    data["expected_returns"] = mu.tolist()
    data["risk_matrix"] = sigma.tolist()
    data["selected_assets_k"] = k
    data["q"] = None if q is None else float(q)
    data["cardinality_penalty_A"] = a
    data["risk_matrix_min_eigenvalue"] = float(np.linalg.eigvalsh(sigma).min())
    data["n_assets"] = 4
    return data

def bitvector_from_int(index: int, n: int = 4) -> np.ndarray:
    return np.asarray([(int(index) >> i) & 1 for i in range(n)], dtype=int)

def base_cost(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray, q: float) -> float:
    """Master Guide objective to minimize: x.T Sigma x - q * mu.T x."""
    xx = np.asarray(x, dtype=float)
    return float(xx @ sigma @ xx - q * (mu @ xx))

def utility(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray, q: float) -> float:
    """Unpenalized objective on the maximization orientation: q*return - risk."""
    return -base_cost(x, mu, sigma, q)

def full_cost(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray, q: float,
              k: int, penalty_a: float) -> float:
    xx = np.asarray(x, dtype=int)
    return base_cost(xx, mu, sigma, q) + penalty_a * (int(xx.sum()) - k) ** 2

def enumerate_solutions(instance: dict[str, Any], penalty_a: float | None = None) -> list[dict[str, Any]]:
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["q"])
    k = int(instance["selected_assets_k"])
    a = float(penalty_a if penalty_a is not None else instance["cardinality_penalty_A"])
    out = []
    for idx in range(1 << len(mu)):
        x = bitvector_from_int(idx, len(mu))
        selected = [instance["assets"][i] for i, b in enumerate(x) if b]
        out.append({
            "bits": x.tolist(),
            "bitstring": "".join(str(int(v)) for v in x[::-1]),
            "selected_assets": selected,
            "selected_count": int(x.sum()),
            "feasible": bool(int(x.sum()) == k),
            "return_component": float(q * (mu @ x)),
            "risk": float(x @ sigma @ x),
            "utility": utility(x, mu, sigma, q),
            "cost": full_cost(x, mu, sigma, q, k, a),
        })
    return out

def qubo_coefficients(mu: np.ndarray, sigma: np.ndarray, q: float, k: int,
                      penalty_a: float) -> tuple[np.ndarray, dict[tuple[int, int], float], float]:
    """Cost = c + sum_i a_i x_i + sum_{i<j} b_ij x_i x_j."""
    mu = np.asarray(mu, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    linear = np.diag(sigma) - q * mu + penalty_a * (1 - 2 * k)
    pair = {(i, j): float(2 * sigma[i, j] + 2 * penalty_a)
            for i in range(len(mu)) for j in range(i + 1, len(mu))}
    constant = float(penalty_a * k * k)
    return linear.astype(float), pair, constant

def qubo_matrix(instance: dict[str, Any]) -> tuple[np.ndarray, float]:
    """Return symmetric Q and c for C(x)=x.T Q x + c."""
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["q"])
    k = int(instance["selected_assets_k"])
    a = float(instance["cardinality_penalty_A"])
    Q = sigma.copy()
    Q[np.diag_indices_from(Q)] = np.diag(sigma) - q * mu + a * (1 - 2 * k)
    for i in range(len(mu)):
        for j in range(i + 1, len(mu)):
            Q[i, j] = Q[j, i] = sigma[i, j] + a
    return Q, float(a * k * k)

def ising_coefficients(linear: np.ndarray, pair: dict[tuple[int, int], float],
                       qubo_constant: float = 0.0):
    """Convert binary QUBO coefficients using x_i=(1-Z_i)/2."""
    linear = np.asarray(linear, dtype=float)
    h = -linear / 2.0
    constant = float(qubo_constant + np.sum(linear) / 2.0)
    j_coeffs = {}
    for (i, j), value in pair.items():
        value = float(value)
        h[i] -= value / 4.0
        h[j] -= value / 4.0
        j_coeffs[(i, j)] = value / 4.0
        constant += value / 4.0
    return h, j_coeffs, constant

def validate_qubo_conversion(instance: dict[str, Any], atol: float = 1e-8) -> None:
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["q"]); k = int(instance["selected_assets_k"])
    a = float(instance["cardinality_penalty_A"]); n = len(mu)
    linear, pair, c = qubo_coefficients(mu, sigma, q, k, a)
    h, j, ising_c = ising_coefficients(linear, pair, c)
    Q, c_matrix = qubo_matrix(instance)
    for idx in range(1 << n):
        x = bitvector_from_int(idx, n).astype(float)
        z = 1.0 - 2.0 * x
        expanded = c + float(linear @ x) + sum(v*x[i]*x[k2] for (i,k2),v in pair.items())
        direct = full_cost(x, mu, sigma, q, k, a)
        matrix_cost = float(x @ Q @ x + c_matrix)
        ising_energy = float(ising_c + h @ z + sum(v*z[i]*z[k2] for (i,k2),v in j.items()))
        if not (np.isclose(expanded, direct, atol=atol, rtol=0) and
                np.isclose(matrix_cost, direct, atol=atol, rtol=0) and
                np.isclose(ising_energy, direct, atol=atol, rtol=0)):
            raise AssertionError(
                f"QUBO/Ising mismatch for x={x.tolist()}: direct={direct}, "
                f"expanded={expanded}, matrix={matrix_cost}, ising={ising_energy}"
            )

# p=1 QAOA implementation is co-located here to match the prescribed repository tree.
from typing import Any
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
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
    if int(restarts) < 1:
        raise ValueError("restarts must be at least 1.")
    if int(maxiter) < 1:
        raise ValueError("maxiter must be at least 1.")
    model=prepare_cost_model(instance); mu=np.asarray(instance["expected_returns"],float); sigma=np.asarray(instance["risk_matrix"],float)
    q=float(instance["q"]); k=int(instance["selected_assets_k"]); a=float(instance["cardinality_penalty_A"]); n=len(mu)
    costs=np.asarray([full_cost(bitvector_from_int(i,n),mu,sigma,q,k,a) for i in range(2**n)],float)
    rng=np.random.default_rng(seed); runs=[]
    for r in range(int(restarts)):
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
    converged=[run for run in runs if run["success"] and np.isfinite(run["expected_scaled_cost"])
               and np.all(np.isfinite([run["gamma"], run["beta"]]))]
    if not converged:
        raise RuntimeError("No QAOA optimizer restart converged to a finite solution.")
    best=min(converged,key=lambda x:x["expected_scaled_cost"])
    return {"gamma":best["gamma"],"beta":best["beta"],"best_restart":best["restart"],
            "best_expected_scaled_cost":best["expected_scaled_cost"],"restarts":runs,"cost_model":model}

def sample_processor(instance: dict[str,Any], params: dict[str,Any], processor: dict[str,Any],
                     mode: str="ideal", noise_model=None, shots: int=SHOTS,
                     seed_simulator: int=TRANSPILER_SEED,
                     initial_layout: list[int] | None = None) -> dict[str,Any]:
    if mode not in {"ideal", "noisy"}:
        raise ValueError("mode must be either 'ideal' or 'noisy'.")
    if int(shots) < 1:
        raise ValueError("shots must be at least 1.")
    if mode == "noisy" and noise_model is None:
        raise ValueError("noisy mode requires an explicit noise_model.")
    logical=build_qaoa_circuit(params["gamma"],params["beta"],params["cost_model"],measured=True)
    swap_count=swap_diagnostic(logical,processor,initial_layout=initial_layout)
    compiled=compile_circuit(logical,processor,initial_layout=initial_layout)
    simulator=AerSimulator(noise_model=noise_model) if mode=="noisy" else AerSimulator()
    result=simulator.run(compiled,shots=int(shots),seed_simulator=int(seed_simulator)).result()
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
            **circuit_metrics(compiled),"shots":int(shots),
            "layout_method":"fixed_initial_layout" if initial_layout is not None else "sabre",
            "initial_layout":list(map(int, initial_layout)) if initial_layout is not None else None,
            "routing_method":"sabre",
            "optimization_level":OPTIMIZATION_LEVEL,"seed_transpiler":TRANSPILER_SEED,"seed_simulator":int(seed_simulator),
            "swap_count_diagnostic":int(swap_count),"valid_portfolio_probability":valid/total,
            "optimal_portfolio_probability":optimal/total,"sampled_expected_utility_all_outcomes":float(util_all),
            "sampled_expected_utility_given_valid":float(util_valid/valid) if valid else None,
            "exact_optimal_utility":exact,"best_sampled_valid_utility":bestu,
            "optimality_gap":None if bestu is None else exact-bestu,"best_sampled_objective_ratio":ratio,
            "optimal_portfolio":optimum["selected_assets"],"best_sampled_valid":best,
            "counts":{str(k):int(v) for k,v in counts.items()},"sampled_distribution":distribution,
            "transpiled_circuit":compiled}
