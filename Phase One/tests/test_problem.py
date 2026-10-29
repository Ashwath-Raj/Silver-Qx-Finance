import json
from pathlib import Path

import numpy as np
import pytest

from src.problem import enumerate_solutions, load_instance, validate_qubo_conversion

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data/processed/portfolio_instance.json"


def load_current_instance():
    return load_instance(CONFIG)


def test_master_guide_inputs_and_all_state_qubo_ising_equivalence():
    instance = load_current_instance()
    assert instance["assets"] == ["Asset_1", "Asset_2", "Asset_3", "Asset_4"]
    assert np.allclose(instance["expected_returns"], [0.12, 0.18, 0.10, 0.22])
    assert np.allclose(instance["risk_matrix"], np.asarray(instance["risk_matrix"]).T)
    assert instance["selected_assets_k"] == 2
    validate_qubo_conversion(instance)


def test_exact_penalized_optimum_is_feasible_for_selected_penalty():
    instance = load_current_instance()
    solutions = enumerate_solutions(instance)
    optimum_cost = min(row["cost"] for row in solutions)
    optima = [row for row in solutions if abs(row["cost"] - optimum_cost) < 1e-10]
    assert optima
    assert all(row["feasible"] for row in optima)
    assert optima[0]["selected_assets"] == ["Asset_1", "Asset_4"]
    assert optimum_cost == pytest.approx(-0.20)


def test_penalty_threshold_tie_is_not_misreported_as_strict_feasibility():
    instance = load_current_instance()
    for penalty in (0.005, 0.01):
        solutions = enumerate_solutions(instance, penalty_a=penalty)
        optimum_cost = min(row["cost"] for row in solutions)
        optima = [row for row in solutions if abs(row["cost"] - optimum_cost) < 1e-10]
        assert any(not row["feasible"] for row in optima)
    solutions = enumerate_solutions(instance, penalty_a=0.02)
    optimum_cost = min(row["cost"] for row in solutions)
    optima = [row for row in solutions if abs(row["cost"] - optimum_cost) < 1e-10]
    assert all(row["feasible"] for row in optima)


@pytest.mark.parametrize("field,value,match", [
    ("q", float("nan"), "finite and positive"),
    ("cardinality_penalty_A", float("inf"), "finite and positive"),
])
def test_nonfinite_scalar_parameters_are_rejected(tmp_path, field, value, match):
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    data[field] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        load_instance(path)


def test_duplicate_asset_names_are_rejected(tmp_path):
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    data["assets"] = ["Asset_1", "Asset_1", "Asset_3", "Asset_4"]
    path = tmp_path / "duplicate_assets.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_instance(path)


def test_nonfinite_model_arrays_are_rejected(tmp_path):
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    data["expected_returns"][0] = float("nan")
    path = tmp_path / "nan_returns.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="finite"):
        load_instance(path)


def test_optimizer_rejects_invalid_work_budget():
    from src.problem import optimize_qaoa
    instance = load_current_instance()
    with pytest.raises(ValueError, match="restarts"):
        optimize_qaoa(instance, restarts=0)
    with pytest.raises(ValueError, match="maxiter"):
        optimize_qaoa(instance, restarts=1, maxiter=0)
