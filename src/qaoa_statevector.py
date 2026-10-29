"""Small, transparent p=1 QAOA statevector prototype for Phase 2 PS-O2.

This intentionally uses a NumPy statevector instead of Qiskit so the algorithm
logic can be unit-tested without a quantum SDK. The required official benchmark
still must use qff_phase2.py for compilation, resource metrics and noisy runs.
"""
from __future__ import annotations
from typing import Any
import numpy as np
from scipy.optimize import minimize
from .classical_reference import all_bitstrings, objective, qubo_energy


def state_bitstrings(n: int) -> list[tuple[int, ...]]:
    """Basis-state labels for statevector index m, with qubit i = bit i of m."""
    return [tuple((mask >> q) & 1 for q in range(n)) for mask in range(2**n)]


def qaoa_state(gamma: float, beta: float, costs: np.ndarray, n_qubits: int) -> np.ndarray:
    """Return normalized p=1 QAOA amplitudes for U_B(beta) U_C(gamma)|+>^n.

    U_C = exp(-i gamma H_C) and U_B = exp(-i beta sum_q X_q). H_C is
    diagonal and `costs[mask]` is the QUBO energy of the bit assignment encoded
    by the integer mask. Each mixer factor exp(-i beta X) is applied directly.
    """
    dim = 1 << n_qubits
    if len(costs) != dim:
        raise ValueError(f"Need {dim} diagonal costs for {n_qubits} qubits")
    psi = np.ones(dim, dtype=np.complex128) / np.sqrt(dim)
    psi *= np.exp(-1j * float(gamma) * np.asarray(costs, dtype=float))
    indices = np.arange(dim)
    c, s = np.cos(float(beta)), np.sin(float(beta))
    for q in range(n_qubits):
        psi = c * psi - 1j * s * psi[indices ^ (1 << q)]
    norm = np.linalg.norm(psi)
    if not np.isclose(norm, 1.0, atol=1e-10):
        raise ArithmeticError(f"Statevector norm drifted to {norm}")
    return psi


def build_costs(instance: dict[str, Any], penalty: float) -> tuple[list[tuple[int, ...]], np.ndarray, np.ndarray]:
    mu=np.asarray(instance['expected_returns'], dtype=float)
    sigma=np.asarray(instance['risk_matrix'], dtype=float)
    q=float(instance['risk_aversion_q']); k=int(instance['k'])
    states=state_bitstrings(len(mu))
    costs=np.asarray([qubo_energy(x,mu,sigma,q,k,float(penalty)) for x in states],dtype=float)
    values=np.asarray([objective(x,mu,sigma,q) for x in states],dtype=float)
    return states,costs,values


def optimize_restarts(instance: dict[str, Any], penalty: float = 2.0,
                      seeds: tuple[int, ...] = (0,1,2,3,4), maxiter: int = 400) -> list[dict[str, Any]]:
    """Optimize expected QUBO energy from reproducible random (gamma,beta) starts."""
    n=len(instance['expected_returns'])
    states,costs,values=build_costs(instance,penalty)
    k=int(instance['k']); mu=np.asarray(instance['expected_returns'],dtype=float)
    sigma=np.asarray(instance['risk_matrix'],dtype=float); q=float(instance['risk_aversion_q'])
    valid_mask=np.asarray([sum(x)==k for x in states],dtype=bool)
    F_star=float(max(values[valid_mask]))
    optimal_mask=valid_mask & np.isclose(values,F_star,atol=1e-10)
    results=[]
    for seed in seeds:
        rng=np.random.default_rng(int(seed))
        x0=rng.uniform(0.0,np.pi,size=2)
        def energy(params):
            g,b=map(float,params)
            psi=qaoa_state(g,b,costs,n)
            probs=np.abs(psi)**2
            return float(probs @ costs)
        result=minimize(energy,x0,method='COBYLA',bounds=[(0,np.pi),(0,np.pi)],
                        options={'maxiter':int(maxiter),'tol':1e-7,'rhobeg':0.5})
        gamma,beta=map(float,result.x)
        psi=qaoa_state(gamma,beta,costs,n)
        probs=np.abs(psi)**2
        valid_probability=float(probs[valid_mask].sum())
        p_opt=float(probs[optimal_mask].sum())
        # Deterministic 4096-shot sample matching the official shot count. The
        # sampled values are still a local NumPy prototype, not an Aer run.
        shot_count=4096
        shot_rng=np.random.default_rng(42)
        sampled_counts=shot_rng.multinomial(shot_count, probs)
        sampled_valid_frequency=float(sampled_counts[valid_mask].sum()/shot_count)
        sampled_p_opt=float(sampled_counts[optimal_mask].sum()/shot_count)
        valid_order=np.flatnonzero(valid_mask)
        sampled_valid_counts=sampled_counts[valid_mask]
        selected_idx=int(valid_order[np.argmax(sampled_valid_counts)])
        selected=states[selected_idx]
        selected_F=float(values[selected_idx])
        # Report exact ideal probabilities, not a finite-shot estimate; sampled
        # metrics belong to the official Phase 2 integration.
        results.append({
            'seed':int(seed),'initial_gamma':float(x0[0]),'initial_beta':float(x0[1]),
            'gamma':gamma,'beta':beta,'optimizer':'COBYLA','max_iterations':int(maxiter),
            'optimization_success':bool(result.success),'optimizer_message':str(result.message),
            'expected_qubo_energy':float(probs @ costs),'valid_probability_ideal_statevector':valid_probability,
            'p_opt_ideal_statevector':p_opt,'shots':shot_count,
            'valid_frequency_sampled_4096':sampled_valid_frequency,'p_opt_sampled_4096':sampled_p_opt,
            'selected_valid_bitstring_sampled_x0_to_x3':''.join(map(str,selected)),
            'selected_valid_assets_zero_based':[i for i,b in enumerate(selected) if b],
            'selected_valid_F_sampled':selected_F,'objective_ratio_selected_valid_sampled':selected_F/F_star,
            'statevector_probabilities':probs.tolist(),
        })
    return results
