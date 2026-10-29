"""Exact classical reference and penalty diagnostics for locked PS-O2.

This module is a transparent, small-instance reference: four binary variables
mean all 16 states can be enumerated exactly. It does not implement QAOA.
"""
from __future__ import annotations

from itertools import product
from typing import Any
import json
from pathlib import Path
import numpy as np


def load_instance(path: str | Path) -> dict[str, Any]:
    """Load the locked PS-O2 input JSON and return the PS-O2 section."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if "PS-O2" in payload:
        payload = payload["PS-O2"]
    required = {"expected_returns", "risk_matrix", "risk_aversion_q", "k", "required_lambda_sweep"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"Missing PS-O2 fields: {sorted(missing)}")
    return payload


def all_bitstrings(n: int) -> list[tuple[int, ...]]:
    """Return all bitstrings as x0..x(n-1), not Qiskit's displayed order."""
    return [tuple(int(bit) for bit in bits) for bits in product((0, 1), repeat=n)]


def objective(x: tuple[int, ...] | list[int], mu: np.ndarray, sigma: np.ndarray, q: float) -> float:
    """Official return-risk objective F(x) = mu^T x - q x^T Sigma x."""
    xv = np.asarray(x, dtype=float)
    return float(mu @ xv - q * (xv @ sigma @ xv))


def qubo_energy(x: tuple[int, ...] | list[int], mu: np.ndarray, sigma: np.ndarray,
                q: float, k: int, penalty: float) -> float:
    """Official minimization objective -F(x) + lambda*(sum(x)-k)^2."""
    xv = np.asarray(x, dtype=float)
    return float(-objective(xv, mu, sigma, q) + penalty * (int(xv.sum()) - k) ** 2)


def qubo_matrix(mu: np.ndarray, sigma: np.ndarray, q: float, k: int, penalty: float) -> tuple[np.ndarray, float]:
    """Return symmetric Q and constant c where x.T@Q@x + c equals QUBO energy.

    For binary x, x_i^2=x_i. Q has diagonal -mu_i + q*Sigma_ii
    + lambda*(1-2k), and off-diagonal q*Sigma_ij + lambda.
    """
    n = len(mu)
    Q = q * np.asarray(sigma, dtype=float).copy()
    Q[np.diag_indices(n)] += -np.asarray(mu, dtype=float) + penalty * (1 - 2 * k)
    for i in range(n):
        for j in range(i + 1, n):
            # Symmetric Q contributes 2*Q_ij*x_i*x_j to x.T Q x.
            Q[i, j] += penalty
            Q[j, i] += penalty
    return Q, float(penalty * k * k)


def enumerate_reference(instance: dict[str, Any]) -> dict[str, Any]:
    """Compute the exact optimum, valid portfolio list, uniform baselines and lambda minima."""
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q, k = float(instance["risk_aversion_q"]), int(instance["k"])
    if sigma.shape != (len(mu), len(mu)) or not np.allclose(sigma, sigma.T):
        raise ValueError("risk_matrix must be square and symmetric")
    states = all_bitstrings(len(mu))
    rows = []
    for x in states:
        rows.append({
            "bitstring_x0_to_xn": "".join(str(b) for b in x),
            "selected_indices": [i for i, b in enumerate(x) if b],
            "selected_count": sum(x),
            "valid": sum(x) == k,
            "F": objective(x, mu, sigma, q),
        })
    valid = [r for r in rows if r["valid"]]
    F_star = max(r["F"] for r in valid)
    opt = [r for r in valid if np.isclose(r["F"], F_star, atol=1e-10)]
    valid_mean_F = float(np.mean([r["F"] for r in valid]))
    all_states_mean_F = float(np.mean([r["F"] for r in rows]))
    uniform_baseline = {
        "number_of_states": len(states),
        "number_of_valid_states": len(valid),
        "valid_frequency": len(valid) / len(states),
        "p_opt": len(opt) / len(states),
        "mean_F_over_all_bitstrings": all_states_mean_F,
        "mean_F_over_valid_bitstrings": valid_mean_F,
        "mean_valid_objective_ratio": valid_mean_F / F_star if F_star else None,
    }
    sweep = []
    for lam in [float(v) for v in instance["required_lambda_sweep"]]:
        scored = [(qubo_energy(tuple(int(c) for c in r["bitstring_x0_to_xn"]), mu, sigma, q, k, lam), r)
                  for r in rows]
        min_energy = min(v for v, _ in scored)
        min_rows = [r for e, r in scored if np.isclose(e, min_energy, atol=1e-10)]
        sweep.append({
            "lambda": lam,
            "min_qubo_energy": float(min_energy),
            "minimizing_bitstrings_x0_to_xn": [r["bitstring_x0_to_xn"] for r in min_rows],
            "all_minima_valid": all(r["valid"] for r in min_rows),
            "any_minimum_valid": any(r["valid"] for r in min_rows),
            "minimum_cardinality_values": sorted({r["selected_count"] for r in min_rows}),
        })
    Q, c = qubo_matrix(mu, sigma, q, k, 2.0)
    return {
        "problem_id": "PS-O2",
        "objective_definition": "F(x) = mu^T x - q * x^T Sigma x",
        "qubo_definition": "E_lambda(x) = -F(x) + lambda * (sum(x) - k)^2",
        "parameters": {"mu": mu.tolist(), "sigma": sigma.tolist(), "q": q, "k": k},
        "state_count": len(states),
        "valid_portfolio_count": len(valid),
        "classical_optimum_F_star": float(F_star),
        "optimal_portfolios": opt,
        "all_valid_portfolios": sorted(valid, key=lambda r: (-r["F"], r["bitstring_x0_to_xn"])),
        "all_states": rows,
        "uniform_random_baseline": uniform_baseline,
        "qubo_matrix_lambda_2": Q.tolist(),
        "qubo_constant_lambda_2": c,
        "exact_penalty_sweep": sweep,
        "scope_note": "This is the exact classical reference and QUBO-minimum diagnostic only; it is not a QAOA sampling result."
    }
