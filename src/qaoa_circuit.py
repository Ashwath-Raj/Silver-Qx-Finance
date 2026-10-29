"""Explicit gate-by-gate p=1 QAOA for the locked Phase 2 PS-O2 instance.

The cost unitary is decomposed from the exact QUBO into RZ and CX gates.
The mixer is implemented as RX(2*beta) on every logical qubit. The constant
Ising term is omitted from the circuit because it contributes only a global
phase; the full constant remains in objective-energy calculations.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from .classical_reference import objective, qubo_energy, qubo_matrix


def qubo_to_ising_coefficients(
    Q: np.ndarray, constant: float = 0.0
) -> tuple[float, np.ndarray, dict[tuple[int, int], float]]:
    """Convert E(x) = x.T @ Q @ x + constant to c + sum(h_i Z_i) + sum(J_ij Z_i Z_j).

    Q must be symmetric. For binary x_i, use x_i = (I - Z_i)/2.
    The returned constant is useful for energy checks; the circuit does not
    need to implement it because it only produces a global phase.
    """
    matrix = np.asarray(Q, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Q must be a square matrix")
    if not np.all(np.isfinite(matrix)) or not np.isfinite(constant):
        raise ValueError("Q and constant must contain only finite values")
    if not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("Q must be symmetric")

    n = matrix.shape[0]
    linear = np.diag(matrix).copy()
    h = -0.5 * linear
    ising_constant = float(constant + 0.5 * linear.sum())
    couplings: dict[tuple[int, int], float] = {}

    for i in range(n):
        for j in range(i + 1, n):
            # x.T @ Q @ x contributes 2*Q[i,j]*x_i*x_j because Q is symmetric.
            pair_coefficient = 2.0 * float(matrix[i, j])
            coupling = pair_coefficient / 4.0
            couplings[(i, j)] = coupling
            h[i] -= pair_coefficient / 4.0
            h[j] -= pair_coefficient / 4.0
            ising_constant += pair_coefficient / 4.0

    return ising_constant, h, couplings


def build_qaoa_p1_circuit(
    instance: dict[str, Any],
    penalty: float,
    gamma: float,
    beta: float,
    *,
    measure: bool = False,
) -> QuantumCircuit:
    """Build p=1 explicitly: H^n, cost RZ/CX gates, then RX mixer.

    Logical qubit i encodes asset i. The QUBO convention and bit ordering match
    src.classical_reference: x = (x0, x1, ..., x[n-1]), with qubit 0 as the
    least-significant bit in statevector indexing and the right-most count bit.
    """
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["risk_aversion_q"])
    k = int(instance["k"])

    if mu.ndim != 1 or sigma.shape != (len(mu), len(mu)):
        raise ValueError("risk_matrix must be square with one row per asset")
    if not np.all(np.isfinite([penalty, gamma, beta])):
        raise ValueError("penalty, gamma and beta must be finite")

    Q, qubo_constant = qubo_matrix(mu, sigma, q, k, float(penalty))
    _, h, couplings = qubo_to_ising_coefficients(Q, qubo_constant)
    n = len(mu)

    qc = QuantumCircuit(n, name=f"qaoa_p1_lambda_{float(penalty):g}")
    qc.h(range(n))

    # U_C(gamma) = exp(-i*gamma*H_C). Since RZ(theta)=exp(-i*theta*Z/2),
    # each h_i Z_i term is RZ(2*gamma*h_i).
    for i, coefficient in enumerate(h):
        if not np.isclose(coefficient, 0.0, atol=1e-15):
            qc.rz(2.0 * float(gamma) * float(coefficient), i)

    # exp(-i*gamma*J_ij*Z_i Z_j) = CX(i,j), RZ_j(2*gamma*J_ij), CX(i,j).
    for (i, j), coefficient in couplings.items():
        if not np.isclose(coefficient, 0.0, atol=1e-15):
            qc.cx(i, j)
            qc.rz(2.0 * float(gamma) * coefficient, j)
            qc.cx(i, j)

    # U_M(beta) = exp(-i*beta*sum_i X_i) = product_i RX_i(2*beta).
    for i in range(n):
        qc.rx(2.0 * float(beta), i)

    if measure:
        qc.measure_all()

    return qc


def exact_statevector_probabilities(
    instance: dict[str, Any], penalty: float, gamma: float, beta: float
) -> np.ndarray:
    """Return ideal probabilities in integer-mask order using Qiskit Statevector."""
    circuit = build_qaoa_p1_circuit(
        instance, penalty, gamma, beta, measure=False
    )
    return np.asarray(Statevector.from_instruction(circuit).probabilities(), dtype=float)


def expected_qubo_energy(
    instance: dict[str, Any], penalty: float, gamma: float, beta: float
) -> tuple[float, np.ndarray]:
    """Calculate the exact expected QUBO energy and return (energy, probabilities)."""
    n = len(instance["expected_returns"])
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["risk_aversion_q"])
    k = int(instance["k"])

    costs = np.empty(1 << n, dtype=float)
    for mask in range(1 << n):
        x = tuple((mask >> i) & 1 for i in range(n))
        costs[mask] = qubo_energy(x, mu, sigma, q, k, float(penalty))

    probabilities = exact_statevector_probabilities(
        instance, penalty, gamma, beta
    )
    if not np.isclose(probabilities.sum(), 1.0, atol=1e-10):
        raise ArithmeticError("Statevector probabilities are not normalized")
    return float(probabilities @ costs), probabilities


def optimize_qaoa_restarts(
    instance: dict[str, Any],
    penalty: float = 2.0,
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    max_function_evaluations: int = 200,
) -> list[dict[str, Any]]:
    """Run reproducible COBYLA starts using exact Qiskit-statevector energy.

    SciPy's COBYLA maxiter option is a maximum function-evaluation budget in
    the supported SciPy API. We therefore record both the requested budget and
    the actual objective evaluation count, along with the termination message.
    """
    if not seeds:
        raise ValueError("At least one initialization seed is required")
    if max_function_evaluations < 1:
        raise ValueError("max_function_evaluations must be positive")

    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["risk_aversion_q"])
    k = int(instance["k"])
    n = len(mu)
    states = [tuple((mask >> i) & 1 for i in range(n)) for mask in range(1 << n)]
    state_values = np.asarray([objective(x, mu, sigma, q) for x in states])
    valid_mask = np.asarray([sum(x) == k for x in states], dtype=bool)
    F_star = float(state_values[valid_mask].max())
    optimal_mask = valid_mask & np.isclose(state_values, F_star, atol=1e-10)

    records: list[dict[str, Any]] = []
    for seed in seeds:
        rng = np.random.default_rng(int(seed))
        initial = rng.uniform(0.0, np.pi, size=2)

        def energy(params: np.ndarray) -> float:
            return expected_qubo_energy(
                instance, penalty, float(params[0]), float(params[1])
            )[0]

        result = minimize(
            energy,
            initial,
            method="COBYLA",
            bounds=[(0.0, np.pi), (0.0, np.pi)],
            options={
                "maxiter": int(max_function_evaluations),
                "rhobeg": 0.5,
                "tol": 1e-7,
            },
        )
        gamma, beta = map(float, result.x)
        final_energy, probabilities = expected_qubo_energy(
            instance, penalty, gamma, beta
        )
        valid_probability = float(probabilities[valid_mask].sum())
        p_opt = float(probabilities[optimal_mask].sum())

        records.append({
            "seed": int(seed),
            "initial_gamma": float(initial[0]),
            "initial_beta": float(initial[1]),
            "gamma": gamma,
            "beta": beta,
            "optimizer": "COBYLA",
            "objective_evaluation_budget": int(max_function_evaluations),
            "objective_evaluations": int(getattr(result, "nfev", 0)),
            "optimizer_iterations": (int(result.nit) if getattr(result, "nit", None) is not None else ""),
            "optimizer_iterations_available": getattr(result, "nit", None) is not None,
            "optimization_success": bool(result.success),
            "stopping_reason": str(result.message),
            "expected_qubo_energy": final_energy,
            "valid_probability_ideal_statevector": valid_probability,
            "p_opt_ideal_statevector": p_opt,
            "classical_optimum_F_star": F_star,
        })

    return records
