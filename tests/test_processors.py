import json
from pathlib import Path

import pytest
from qiskit import QuantumCircuit

from src.metrics import circuit_metrics
from src.processors import (
    ALTERNATIVE_TOPOLOGIES, load_processor, make_topology_variant,
    topology_metrics, build_synthetic_noise_model,
)
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

@pytest.mark.parametrize("filename,expected_edges", [
    ("processor_A.json", 8),
    ("processor_B.json", 16),
])
def test_paca_custom_topologies_are_valid_and_preserve_reference_configs(filename, expected_edges):
    processor = load_processor(ROOT / "processors" / filename)
    spec = ALTERNATIVE_TOPOLOGIES[processor["name"]]
    variant = make_topology_variant(processor, spec["label"], spec["edges"])
    metrics = topology_metrics(variant)
    assert metrics["connected"]
    assert metrics["num_qubits"] == processor["num_qubits"]
    assert metrics["edge_count"] == expected_edges
    assert not variant["is_reference_graph"]
    assert variant["topology_type"] == "participant_designed_custom_supplementary"
    # The complete K4 core supports all pairwise interactions between four variables.
    core_edges = {tuple(sorted(edge)) for edge in spec["edges"] if edge[0] < 4 and edge[1] < 4}
    assert core_edges == {(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)}
    # In-memory alternatives never mutate the authoritative reference object.
    assert processor["is_reference_graph"]
    assert len(processor["coupling_edges_undirected"]) == (4 if filename == "processor_A.json" else 12)


@pytest.mark.parametrize("filename", ["processor_A.json", "processor_B.json"])
def test_fixed_k4_layout_compiles_pairwise_interactions_without_layout_drift(filename):
    processor = load_processor(ROOT / "processors" / filename)
    spec = ALTERNATIVE_TOPOLOGIES[processor["name"]]
    variant = make_topology_variant(processor, spec["label"], spec["edges"])
    logical = QuantumCircuit(4)
    logical.h(range(4))
    for i in range(4):
        for j in range(i + 1, 4):
            logical.rzz(0.17 + 0.03 * (i + j), i, j)
    compiled = compile_circuit(logical, variant, initial_layout=[0, 1, 2, 3])
    assert compiled.num_qubits == processor["num_qubits"]
    assert set(compiled.count_ops()).issubset(set(BASIS_GATES))
    assert compiled.layout is not None
    mapped = compiled.layout.initial_layout.get_virtual_bits()
    for virtual_index, physical_index in enumerate([0, 1, 2, 3]):
        assert mapped[logical.qubits[virtual_index]] == physical_index


@pytest.mark.parametrize("bad_layout", [[0, 1, 2], [0, 1, 1, 3], [0, 1, 2, 5]])
def test_invalid_explicit_layouts_are_rejected(bad_layout):
    processor = load_processor(ROOT / "processors/processor_A.json")
    variant = make_topology_variant(processor, "test", ALTERNATIVE_TOPOLOGIES["Processor A"]["edges"])
    with pytest.raises(ValueError, match="initial_layout"):
        compile_circuit(QuantumCircuit(4), variant, initial_layout=bad_layout)
