import json
from pathlib import Path

import pytest
from qiskit import QuantumCircuit

from src.metrics import circuit_metrics
from src.processors import load_processor, topology_metrics, build_synthetic_noise_model
from src.routing import BASIS_GATES, compile_circuit

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename,n_qubits,n_edges", [
    ("processor_A.json", 5, 4),
    ("processor_B.json", 9, 12),
])
def test_reference_processor_maps_are_connected_and_have_expected_size(filename, n_qubits, n_edges):
    processor = load_processor(ROOT / "processors" / filename)
    metrics = topology_metrics(processor)
    assert processor["is_reference_graph"]
    assert metrics["connected"]
    assert metrics["num_qubits"] == n_qubits
    assert metrics["edge_count"] == n_edges


@pytest.mark.parametrize("filename", ["processor_A.json", "processor_B.json"])
def test_compiler_maps_logical_entanglement_to_native_basis(filename):
    processor = load_processor(ROOT / "processors" / filename)
    logical = QuantumCircuit(4)
    logical.h(range(4))
    logical.rzz(0.37, 0, 3)
    logical.rzz(0.19, 1, 2)
    compiled = compile_circuit(logical, processor)
    assert compiled.num_qubits == processor["num_qubits"]
    assert set(compiled.count_ops()).issubset(set(BASIS_GATES))
    metrics = circuit_metrics(compiled)
    assert metrics["depth"] > 0
    assert metrics["cx_count"] > 0
    assert metrics["swap_count_native"] == 0
    assert metrics["physical_qubits_touched"] <= processor["num_qubits"]


def test_disconnected_processor_graph_is_rejected(tmp_path):
    data = json.loads((ROOT / "processors/processor_A.json").read_text(encoding="utf-8"))
    data["coupling_edges_undirected"] = [[0, 1], [1, 2], [0, 2], [3, 4]]
    path = tmp_path / "disconnected.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="connected"):
        load_processor(path)


def test_noise_model_can_be_constructed():
    model = build_synthetic_noise_model()
    assert model is not None
    assert "cx" in model.basis_gates
