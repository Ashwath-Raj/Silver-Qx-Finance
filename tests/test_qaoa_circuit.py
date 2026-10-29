from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector

from src.classical_reference import (
    all_bitstrings,
    load_instance,
    qubo_energy,
    qubo_matrix,
)
from src.qaoa_circuit import (
    build_qaoa_p1_circuit,
    qubo_to_ising_coefficients,
)
from src.qaoa_statevector import build_costs, qaoa_state

ROOT = Path(__file__).resolve().parents[1]


def test_ising_coefficients_reproduce_qubo_energy_for_all_16_states():
    instance = load_instance(ROOT / "data/instance.json")
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    Q, constant = qubo_matrix(
        mu, sigma, float(instance["risk_aversion_q"]), int(instance["k"]), 2.0
    )
    c_ising, h, couplings = qubo_to_ising_coefficients(Q, constant)

    for x in all_bitstrings(4):
        z = 1.0 - 2.0 * np.asarray(x, dtype=float)
        energy_ising = c_ising + float(h @ z)
        energy_ising += sum(value * z[i] * z[j] for (i, j), value in couplings.items())
        energy_qubo = qubo_energy(
            x, mu, sigma, float(instance["risk_aversion_q"]), int(instance["k"]), 2.0
        )
        assert np.isclose(energy_ising, energy_qubo, atol=1e-9)


def test_explicit_qiskit_circuit_probabilities_match_numpy_reference():
    instance = load_instance(ROOT / "data/instance.json")
    gamma, beta, penalty = 0.43, 1.17, 2.0
    _, costs, _ = build_costs(instance, penalty)
    numpy_amplitudes = qaoa_state(gamma, beta, costs, n_qubits=4)
    circuit = build_qaoa_p1_circuit(
        instance, penalty=penalty, gamma=gamma, beta=beta, measure=False
    )
    qiskit_probabilities = Statevector.from_instruction(circuit).probabilities()

    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 0
    assert np.allclose(qiskit_probabilities, np.abs(numpy_amplitudes) ** 2, atol=1e-9)
    assert np.isclose(float(qiskit_probabilities.sum()), 1.0, atol=1e-10)


def test_explicit_circuit_can_add_measurements_without_changing_logical_width():
    instance = load_instance(ROOT / "data/instance.json")
    circuit = build_qaoa_p1_circuit(
        instance, penalty=2.0, gamma=0.4, beta=0.8, measure=True
    )
    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 4
    assert circuit.count_ops().get("measure", 0) == 4
