"""Low-level p=1 QAOA implementation for QFF O2.

Uses Qiskit circuits directly rather than optional Qiskit Optimization modules,
which keeps the implementation transparent and easier to audit.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit.transpiler import CouplingMap, Layout, PassManager
from qiskit.transpiler.passes import (
    ApplyLayout,
    BasicSwap,
    EnlargeWithAncilla,
    FullAncillaAllocation,
    SetLayout,
)
from qiskit_aer import AerSimulator

from .portfolio_model import (
    bitvector_from_int,
    enumerate_solutions,
    full_cost,
    ising_coefficients,
    qubo_coefficients,
    utility,
)


def prepare_cost_model(instance: dict[str, Any], penalty: float) -> dict[str, Any]:
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    risk_weight = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    linear, pair, qubo_constant = qubo_coefficients(returns, risk, risk_weight, k, penalty)
    h, j_coeffs, ising_constant = ising_coefficients(linear, pair)
    max_abs = max(
        float(np.max(np.abs(h))) if h.size else 0.0,
        max((abs(v) for v in j_coeffs.values()), default=0.0),
        1e-12,
    )
    return {
        "linear": linear,
        "pair": pair,
        "qubo_constant": qubo_constant,
        "h": h,
        "j": j_coeffs,
        "ising_constant": ising_constant + qubo_constant,
        "phase_scale": max_abs,
    }


def build_qaoa_circuit(
    gamma: float,
    beta: float,
    cost_model: dict[str, Any],
    measured: bool = False,
) -> QuantumCircuit:
    """Build one p=1 QAOA layer using RZ/RZZ cost evolution and RX mixer."""
    n = len(cost_model["h"])
    qc = QuantumCircuit(n, n) if measured else QuantumCircuit(n)
    qc.h(range(n))
    scale = float(cost_model["phase_scale"])

    # exp(-i * gamma * H_cost / scale). Constant terms are global phase and omitted.
    for i, coeff in enumerate(cost_model["h"]):
        qc.rz(2.0 * gamma * float(coeff) / scale, i)
    for (i, j), coeff in cost_model["j"].items():
        qc.rzz(2.0 * gamma * float(coeff) / scale, i, j)

    # exp(-i * beta * sum(X_i)) = product_i RX_i(2 beta).
    for i in range(n):
        qc.rx(2.0 * beta, i)

    if measured:
        qc.measure(range(n), range(n))
    return qc


def exact_expected_scaled_cost(
    params: np.ndarray,
    cost_model: dict[str, Any],
    instance: dict[str, Any],
    penalty: float,
) -> float:
    """Exact-statevector expected cost divided by a positive scale for stability."""
    gamma, beta = float(params[0]), float(params[1])
    circuit = build_qaoa_circuit(gamma, beta, cost_model, measured=False)
    probs = Statevector.from_instruction(circuit).probabilities()
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    lam = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    n = len(returns)
    costs = np.asarray([
        full_cost(bitvector_from_int(i, n), returns, risk, lam, k, penalty)
        for i in range(2**n)
    ], dtype=float)
    # A positive affine scaling leaves the argmin unchanged.
    return float(np.dot(probs, costs) / cost_model["phase_scale"])


def optimize_qaoa(
    instance: dict[str, Any],
    penalty: float,
    restarts: int = 6,
    maxiter: int = 300,
    seed: int = 2026,
) -> dict[str, Any]:
    """Optimize p=1 QAOA parameters using reproducible multi-start Nelder-Mead."""
    cost_model = prepare_cost_model(instance, penalty)
    rng = np.random.default_rng(seed)
    bounds = [(0.0, 2.0 * np.pi), (0.0, np.pi)]
    runs: list[dict[str, Any]] = []
    for restart in range(max(1, int(restarts))):
        if restart == 0:
            x0 = np.asarray([0.7, 0.4], dtype=float)
        else:
            x0 = np.asarray([rng.uniform(*bounds[0]), rng.uniform(*bounds[1])])
        result = minimize(
            exact_expected_scaled_cost,
            x0=x0,
            args=(cost_model, instance, penalty),
            method="Nelder-Mead",
            bounds=bounds,
            options={"maxiter": int(maxiter), "xatol": 1e-4, "fatol": 1e-5},
        )
        runs.append({
            "restart": restart,
            "gamma": float(result.x[0]),
            "beta": float(result.x[1]),
            "expected_scaled_cost": float(result.fun),
            "success": bool(result.success),
            "message": str(result.message),
            "iterations": int(getattr(result, "nit", -1)),
            "function_evaluations": int(getattr(result, "nfev", -1)),
        })

    best = min(runs, key=lambda item: item["expected_scaled_cost"])
    return {
        "gamma": best["gamma"],
        "beta": best["beta"],
        "best_expected_scaled_cost": best["expected_scaled_cost"],
        "best_restart": best["restart"],
        "restarts": runs,
        "cost_model": cost_model,
    }


def coupling_map_from_processor(processor: dict[str, Any]) -> CouplingMap:
    """Build a symmetric directed coupling map from the unique undirected edges."""
    directed = []
    for left, right in processor["coupling_edges_undirected"]:
        directed.append((int(left), int(right)))
        directed.append((int(right), int(left)))
    coupling = CouplingMap(couplinglist=directed)
    expected = int(processor["num_qubits"])
    if coupling.size() != expected:
        raise ValueError(f"{processor['name']} topology has {coupling.size()} qubits, expected {expected}.")
    return coupling


def count_basic_routing_swaps(
    circuit: QuantumCircuit, processor: dict[str, Any]
) -> int:
    """Count SWAP gates inserted by Qiskit's BasicSwap pass with a fixed initial layout.

    This is a routing diagnostic, not an optimized-layout result. Logical qubits
    0..n-1 start on physical qubits 0..n-1 for both devices, making the baseline
    placement rule reproducible. The execution circuit is transpiled separately.
    """
    coupling = coupling_map_from_processor(processor)
    initial_layout = Layout({q: i for i, q in enumerate(circuit.qubits)})
    pm = PassManager([
        SetLayout(initial_layout),
        FullAncillaAllocation(coupling),
        EnlargeWithAncilla(),
        ApplyLayout(),
        BasicSwap(coupling),
    ])
    routed = pm.run(circuit.remove_final_measurements(inplace=False))
    return int(routed.count_ops().get("swap", 0))


def transpile_for_processor(
    circuit: QuantumCircuit,
    processor: dict[str, Any],
    seed: int = 2026,
    optimization_level: int = 0,
) -> QuantumCircuit:
    """Transpile under a fixed trivial layout/basic routing baseline."""
    coupling = coupling_map_from_processor(processor)
    return transpile(
        circuit,
        coupling_map=coupling,
        basis_gates=list(processor["basis_gates"]),
        layout_method="trivial",
        routing_method="basic",
        optimization_level=int(optimization_level),
        seed_transpiler=int(seed),
    )


def sample_processor(
    instance: dict[str, Any],
    penalty: float,
    parameters: dict[str, Any],
    processor: dict[str, Any],
    shots: int,
    seed: int,
) -> dict[str, Any]:
    """Transpile and sample the chosen QAOA parameters on an ideal Aer simulator."""
    cost_model = parameters["cost_model"]
    measured_logical = build_qaoa_circuit(
        parameters["gamma"], parameters["beta"], cost_model, measured=True
    )
    # Explicit swap count comes from the router before basis translation.
    swap_count = count_basic_routing_swaps(measured_logical, processor)
    compiled = transpile_for_processor(measured_logical, processor, seed=seed, optimization_level=0)
    simulator = AerSimulator()
    result = simulator.run(compiled, shots=int(shots), seed_simulator=int(seed)).result()
    counts = result.get_counts(compiled)

    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    lam = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    n = len(returns)
    total_shots = sum(counts.values())
    valid_shots = 0
    optimal_shots = 0
    expected_utility_all_samples = 0.0
    valid_utility_sum = 0.0
    sampled_records: list[dict[str, Any]] = []
    classical_solutions = enumerate_solutions(instance, penalty)
    feasible = [s for s in classical_solutions if s["feasible"]]
    optimum = max(feasible, key=lambda s: s["utility"])
    optimal_key = optimum["bitstring"]
    best_sampled: dict[str, Any] | None = None

    for key, count in counts.items():
        bitstring = key.replace(" ", "")
        x = np.asarray([int(bitstring[-1 - i]) for i in range(n)], dtype=int)
        is_valid = int(x.sum()) == k
        u = utility(x, returns, risk, lam)
        prob = count / total_shots
        expected_utility_all_samples += prob * u
        if is_valid:
            valid_shots += count
            valid_utility_sum += count * u
            if bitstring == optimal_key:
                optimal_shots += count
            candidate = {
                "bitstring": bitstring,
                "bits": x.tolist(),
                "selected_assets": [instance["assets"][i] for i, bit in enumerate(x) if bit],
                "utility": float(u),
                "count": int(count),
                "probability": float(prob),
            }
            if best_sampled is None or candidate["utility"] > best_sampled["utility"]:
                best_sampled = candidate
        sampled_records.append({
            "bitstring": bitstring,
            "bits": x.tolist(),
            "count": int(count),
            "probability": float(prob),
            "valid": bool(is_valid),
            "utility": float(u),
        })

    opt_utility = float(optimum["utility"])
    best_utility = None if best_sampled is None else float(best_sampled["utility"])
    optimality_gap = None if best_utility is None else float(opt_utility - best_utility)
    ratio = None
    # A raw objective ratio is meaningful only when both values are positive.
    # Otherwise rely on the absolute optimality gap and state why the ratio is omitted.
    if best_utility is not None and opt_utility > 1e-12 and best_utility >= 0.0:
        ratio = float(best_utility / opt_utility)

    ops = compiled.count_ops()
    physical_used = sorted({compiled.find_bit(q).index for instr in compiled.data for q in instr.qubits})
    return {
        "processor": processor["name"],
        "processor_qubits": int(processor["num_qubits"]),
        "compiled_qubits": int(compiled.num_qubits),
        "physical_qubits_touched": len(physical_used),
        "layout_method": "trivial",
        "routing_method": "basic",
        "optimization_level": 0,
        "shots": int(shots),
        "depth": int(compiled.depth()),
        "cx_count": int(ops.get("cx", 0)),
        "swap_count_basic_routing": int(swap_count),
        "valid_portfolio_probability": float(valid_shots / total_shots),
        "optimal_portfolio_probability": float(optimal_shots / total_shots),
        "sampled_expected_utility_all_outcomes": float(expected_utility_all_samples),
        "sampled_expected_utility_given_valid": (float(valid_utility_sum / valid_shots) if valid_shots else None),
        "exact_optimal_utility": opt_utility,
        "best_sampled_valid_utility": best_utility,
        "optimality_gap": optimality_gap,
        "best_sampled_objective_ratio": ratio,
        "optimal_bitstring": optimal_key,
        "best_sampled_valid": best_sampled,
        "counts": {str(k): int(v) for k, v in counts.items()},
        "sampled_distribution": sampled_records,
        "transpiled_circuit": compiled,
    }
