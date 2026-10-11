"""Classical portfolio objective and QUBO/Ising conversion helpers.

The functions in this module deliberately use NumPy only so the problem
formulation can be validated independently of the Qiskit installation.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np


def load_instance(path: str | Path) -> dict[str, Any]:
    """Load and validate the problem instance from JSON."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    assets = data.get("assets")
    returns = np.asarray(data.get("expected_returns"), dtype=float)
    risk = np.asarray(data.get("risk_matrix"), dtype=float)
    k = int(data.get("selected_assets_k"))
    lam = float(data.get("risk_weight_lambda"))

    if not isinstance(assets, list) or len(assets) == 0:
        raise ValueError("'assets' must be a non-empty list.")
    n = len(assets)
    if returns.shape != (n,):
        raise ValueError(f"expected_returns must have shape ({n},); got {returns.shape}.")
    if risk.shape != (n, n):
        raise ValueError(f"risk_matrix must have shape ({n}, {n}); got {risk.shape}.")
    if not np.allclose(risk, risk.T, atol=1e-10):
        raise ValueError("risk_matrix must be symmetric.")
    if np.linalg.eigvalsh(risk).min() < -1e-8:
        raise ValueError("risk_matrix must be positive semidefinite for this covariance-style model.")
    if not (0 <= k <= n):
        raise ValueError("selected_assets_k must be between 0 and the number of assets.")
    if lam < 0:
        raise ValueError("risk_weight_lambda must be non-negative.")

    data["n_assets"] = n
    data["expected_returns"] = returns.tolist()
    data["risk_matrix"] = risk.tolist()
    data["selected_assets_k"] = k
    data["risk_weight_lambda"] = lam
    data["risk_matrix_min_eigenvalue"] = float(np.linalg.eigvalsh(risk).min())
    if data.get("penalty_weight") is not None:
        data["penalty_weight"] = float(data["penalty_weight"])
    return data


def bitvector_from_int(index: int, n: int) -> np.ndarray:
    """Convert an integer basis-state index to x_0,...,x_(n-1) bits.

    Qiskit basis-state indexing is little-endian: qubit 0 is bit 0.
    """
    return np.asarray([(index >> i) & 1 for i in range(n)], dtype=int)


def base_cost(x: np.ndarray, returns: np.ndarray, risk: np.ndarray, risk_weight: float) -> float:
    """Unconstrained cost to minimize: -return + risk_weight * portfolio risk."""
    x_float = np.asarray(x, dtype=float)
    return float(-returns @ x_float + risk_weight * (x_float @ risk @ x_float))


def utility(x: np.ndarray, returns: np.ndarray, risk: np.ndarray, risk_weight: float) -> float:
    """Return-risk utility to maximize, before the cardinality penalty."""
    return -base_cost(x, returns, risk, risk_weight)


def choose_penalty_weight(
    returns: np.ndarray, risk: np.ndarray, risk_weight: float, n: int
) -> float:
    """Choose P larger than the complete range of the unpenalized objective.

    This ensures any infeasible cardinality choice cannot beat every feasible
    choice in this finite instance. It is a principled baseline, not a universal
    optimal QAOA penalty; overly large penalties can still make parameter
    optimization harder.
    """
    values = [base_cost(bitvector_from_int(i, n), returns, risk, risk_weight) for i in range(2**n)]
    span = max(values) - min(values)
    return float(max(1.0, span + 1.0))


def full_cost(
    x: np.ndarray,
    returns: np.ndarray,
    risk: np.ndarray,
    risk_weight: float,
    k: int,
    penalty: float,
) -> float:
    """QUBO cost to minimize, including an exact-cardinality penalty."""
    x_arr = np.asarray(x, dtype=int)
    return base_cost(x_arr, returns, risk, risk_weight) + penalty * (int(x_arr.sum()) - k) ** 2


def enumerate_solutions(instance: dict[str, Any], penalty: float) -> list[dict[str, Any]]:
    """Enumerate all 2**n selections and return objective and feasibility data."""
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    lam = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    n = len(returns)
    solutions: list[dict[str, Any]] = []
    for idx in range(2**n):
        x = bitvector_from_int(idx, n)
        selected = [instance["assets"][i] for i, bit in enumerate(x) if bit]
        solutions.append({
            "bits": x.tolist(),
            "bitstring": "".join(str(int(v)) for v in x[::-1]),
            "selected_assets": selected,
            "selected_count": int(x.sum()),
            "feasible": bool(int(x.sum()) == k),
            "utility": utility(x, returns, risk, lam),
            "cost": full_cost(x, returns, risk, lam, k, penalty),
        })
    return solutions


def qubo_coefficients(
    returns: np.ndarray,
    risk: np.ndarray,
    risk_weight: float,
    k: int,
    penalty: float,
) -> tuple[np.ndarray, dict[tuple[int, int], float], float]:
    """Return QUBO coefficients for cost = c + sum(a_i x_i) + sum(b_ij x_i x_j).

    Only i < j pair coefficients are returned. The constant has no effect on
    QAOA's phase separator, but it is returned for validation/reporting.
    """
    returns = np.asarray(returns, dtype=float)
    risk = np.asarray(risk, dtype=float)
    n = len(returns)
    linear = -returns + risk_weight * np.diag(risk) + penalty * (1 - 2 * k)
    pair: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            # x.T @ risk @ x contains 2 * risk[i,j] * x_i*x_j for symmetric risk.
            pair[(i, j)] = float(2 * risk_weight * risk[i, j] + 2 * penalty)
    constant = float(penalty * k * k)
    return linear.astype(float), pair, constant


def ising_coefficients(
    linear: np.ndarray, pair: dict[tuple[int, int], float]
) -> tuple[np.ndarray, dict[tuple[int, int], float], float]:
    """Convert QUBO coefficients to H = constant + sum(h_i Z_i) + sum(J_ij Z_i Z_j).

    Uses x_i = (1 - Z_i)/2. The returned constant is irrelevant to the QAOA
    state, but keeping it makes the conversion independently testable.
    """
    linear = np.asarray(linear, dtype=float)
    n = len(linear)
    h = -linear / 2.0
    constant = float(np.sum(linear) / 2.0)
    j_coeffs: dict[tuple[int, int], float] = {}
    for (i, j), value in pair.items():
        value = float(value)
        h[i] -= value / 4.0
        h[j] -= value / 4.0
        j_coeffs[(i, j)] = value / 4.0
        constant += value / 4.0
    return h, j_coeffs, constant


def validate_qubo_conversion(instance: dict[str, Any], penalty: float, atol: float = 1e-8) -> None:
    """Assert expanded QUBO agrees with direct cost evaluation for all bitstrings."""
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    lam = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    n = len(returns)
    linear, pair, constant = qubo_coefficients(returns, risk, lam, k, penalty)
    for idx in range(2**n):
        x = bitvector_from_int(idx, n).astype(float)
        q = constant + float(linear @ x)
        q += sum(value * x[i] * x[j] for (i, j), value in pair.items())
        direct = full_cost(x, returns, risk, lam, k, penalty)
        if not np.isclose(q, direct, atol=atol, rtol=0):
            raise AssertionError(f"QUBO mismatch for x={x.tolist()}: expanded={q}, direct={direct}")

    h, j_coeffs, ising_constant = ising_coefficients(linear, pair)
    for idx in range(2**n):
        x = bitvector_from_int(idx, n)
        z = 1 - 2 * x
        energy = (ising_constant + constant) + float(h @ z)
        energy += sum(v * z[i] * z[j] for (i, j), v in j_coeffs.items())
        direct = constant + float(linear @ x)
        direct += sum(v * x[i] * x[j] for (i, j), v in pair.items())
        if not np.isclose(energy, direct, atol=atol, rtol=0):
            raise AssertionError(f"Ising conversion mismatch for x={x.tolist()}: Ising={energy}, QUBO={direct}")
