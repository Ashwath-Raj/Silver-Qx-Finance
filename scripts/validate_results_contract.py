#!/usr/bin/env python3
"""Validate QFF PS-O2 result schema, required run coverage and cross-artifact consistency.

The first 18 columns follow the organizer's Section 9 order. PS-O2 appends lambda
and explicitly named metric/baseline columns so both the validity-score formula and
objective-ratio analysis can be checked without inferring values from another file.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
BASE_COLUMNS = [
    "problem_id", "processor", "condition", "executable", "logical_qubits",
    "physical_qubits", "logical_cx", "cx", "depth", "two_q_depth", "swaps",
    "cx_overhead", "shots", "quality_metric", "quality_value", "p_opt",
    "classical_optimum", "random_baseline",
]
EXTENSION_COLUMNS = [
    "lambda", "valid_solution_frequency", "objective_ratio_selected_valid",
    "random_baseline_valid_frequency", "random_baseline_p_opt",
    "random_baseline_objective_ratio",
]
LAMBDA_VALUES = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"RESULT CONTRACT FAIL: {message}")


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    path = TABLES / name
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None, f"missing CSV header in {name}")
        rows = list(reader)
        return list(reader.fieldnames), rows


def number(row: dict[str, str], field: str, where: str) -> float:
    value = row.get(field, "")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise SystemExit(f"RESULT CONTRACT FAIL: {where}.{field} is not numeric: {value!r}")
    require(math.isfinite(result), f"{where}.{field} is not finite")
    return result


def close(actual: float, expected: float, where: str, tol: float = 2e-9) -> None:
    require(math.isclose(actual, expected, rel_tol=tol, abs_tol=tol),
            f"{where}: expected {expected:.12g}, got {actual:.12g}")


def key(row: dict[str, str]) -> tuple[str, str, float]:
    return (row["processor"], row["condition"], number(row, "lambda", "results.csv row"))


def main() -> int:
    headers, rows = read_csv("results.csv")
    require(headers[:len(BASE_COLUMNS)] == BASE_COLUMNS,
            "results.csv must preserve the organizer's 18 required columns in the specified order")
    require(headers[len(BASE_COLUMNS):len(BASE_COLUMNS) + len(EXTENSION_COLUMNS)] == EXTENSION_COLUMNS,
            "PS-O2 extension columns must be lambda, valid_solution_frequency, objective_ratio_selected_valid, "
            "random_baseline_valid_frequency, random_baseline_p_opt, random_baseline_objective_ratio")
    require(len(rows) == 16, f"expected 16 PS-O2 result rows (6 at lambda=2 plus 10 extra D sweep rows), got {len(rows)}")

    expected = {
        (processor, condition, 2.0)
        for processor in ("Processor A", "Processor B", "Processor D")
        for condition in ("ideal", "noisy")
    }
    expected |= {
        ("Processor D", condition, lam)
        for lam in LAMBDA_VALUES if lam != 2.0
        for condition in ("ideal", "noisy")
    }
    actual = [key(row) for row in rows]
    require(len(actual) == len(set(actual)), "duplicate processor × condition × lambda result rows")
    require(set(actual) == expected, f"required coverage mismatch; missing={sorted(expected-set(actual))}; extra={sorted(set(actual)-expected)}")

    result_by_key = {key(row): row for row in rows}
    random_valid = 6.0 / 16.0
    random_opt = 1.0 / 16.0
    random_ratio = 3.625 / 4.75
    for i, row in enumerate(rows, start=2):
        where = f"results.csv line {i}"
        require(row["problem_id"] == "PS-O2", f"{where}: unexpected problem_id")
        require(row["condition"] in {"ideal", "noisy"}, f"{where}: invalid condition")
        require(row["executable"].lower() == "true", f"{where}: PS-O2 processor should be executable")
        close(number(row, "shots", where), 4096.0, where + ".shots")
        require(row["quality_metric"] == "valid_solution_frequency",
                f"{where}: quality_metric must be valid_solution_frequency to match the PS-O2 scoring formula")
        valid = number(row, "valid_solution_frequency", where)
        close(number(row, "quality_value", where), valid, where + ".quality_value")
        close(number(row, "random_baseline", where), random_valid, where + ".random_baseline(valid frequency)")
        close(number(row, "random_baseline_valid_frequency", where), random_valid, where + ".random_baseline_valid_frequency")
        close(number(row, "random_baseline_p_opt", where), random_opt, where + ".random_baseline_p_opt")
        close(number(row, "random_baseline_objective_ratio", where), random_ratio, where + ".random_baseline_objective_ratio")
        close(number(row, "classical_optimum", where), 4.75, where + ".classical_optimum")
        p_opt = number(row, "p_opt", where)
        ratio = number(row, "objective_ratio_selected_valid", where)
        require(0 <= valid <= 1 and 0 <= p_opt <= 1, f"{where}: probabilities must be in [0,1]")
        require(0 <= ratio <= 1, f"{where}: objective ratio must be in [0,1]")

    condition_headers, condition_rows = read_csv("processor_conditions.csv")
    condition_by_key = {
        (r["processor"], r["condition"], number(r, "lambda", "processor_conditions.csv")): r
        for r in condition_rows
    }
    require(len(condition_by_key) == 6, f"processor_conditions.csv should have six reference-penalty rows, got {len(condition_by_key)}")
    for row_key, detail in condition_by_key.items():
        where = f"processor_conditions.csv {row_key}"
        close(number(detail, "objective_ratio_selected_valid", where),
              number(detail, "selected_F", where) / number(detail, "classical_optimum_F_star", where),
              where + ".objective ratio")

    sweep_headers, sweep_rows = read_csv("processor_d_lambda_sweep.csv")
    sweep_by_key = {
        (r["processor"], r["condition"], number(r, "lambda", "processor_d_lambda_sweep.csv")): r
        for r in sweep_rows
    }
    require(len(sweep_by_key) == 12, f"processor_d_lambda_sweep.csv should have 12 rows, got {len(sweep_by_key)}")
    for row_key, detail in sweep_by_key.items():
        where = f"processor_d_lambda_sweep.csv {row_key}"
        selected_f = number(detail, "selected_F", where)
        optimum_f = number(detail, "classical_optimum_F_star", where)
        close(number(detail, "objective_ratio_selected_valid", where), selected_f / optimum_f,
              where + ".objective ratio")

    for row_key, result in result_by_key.items():
        detail = condition_by_key.get(row_key) if row_key[2] == 2.0 else sweep_by_key.get(row_key)
        require(detail is not None, f"no detailed metrics for {row_key}")
        for field in ("valid_solution_frequency", "p_opt", "objective_ratio_selected_valid"):
            close(number(result, field, "results.csv"), number(detail, field, "detail table"), f"{row_key}.{field}")

    # The exact QUBO minimum must be invalid at lambda 0 and 0.5 and valid thereafter.
    for lam in LAMBDA_VALUES:
        expected_valid = lam >= 1.0
        for condition in ("ideal", "noisy"):
            row = sweep_by_key[("Processor D", condition, lam)]
            actual_valid = row["qubo_minimum_valid"].strip().lower() == "true"
            require(actual_valid == expected_valid,
                    f"QUBO minimum feasibility at lambda={lam:g}, {condition}: expected {expected_valid}, got {row['qubo_minimum_valid']!r}")

    bell_headers, bell_rows = read_csv("bell.csv")
    require(len(bell_rows) == 4, f"bell.csv should have four aggregate rows, got {len(bell_rows)}")
    bell_keys = {(r["pair_type"], r["condition"]) for r in bell_rows}
    expected_bell = {(pair, condition) for pair in ("adjacent", "farthest") for condition in ("ideal", "noisy")}
    require(bell_keys == expected_bell, f"bell.csv coverage mismatch: {bell_keys}")
    for i, row in enumerate(bell_rows, start=2):
        where = f"bell.csv line {i}"
        require(row.get("processor") == "Processor D", f"{where}: unexpected processor")
        close(number(row, "shots", where), 4096.0, where + ".shots")
        expected_distance = 1.0 if row["pair_type"] == "adjacent" else 3.0
        close(number(row, "pair_distance", where), expected_distance, where + ".pair_distance")
        xx, yy, zz = (number(row, field, where) for field in ("XX", "YY", "ZZ"))
        fidelity = number(row, "fidelity", where)
        close(fidelity, (1.0 + xx - yy + zz) / 4.0, where + ".fidelity")
        expected_se = math.sqrt(sum(number(row, field, where) ** 2 for field in ("XX_se", "YY_se", "ZZ_se"))) / 4.0
        close(number(row, "fidelity_se", where), expected_se, where + ".fidelity_se")
        if row["condition"] == "ideal":
            close(xx, 1.0, where + ".XX ideal")
            close(yy, -1.0, where + ".YY ideal")
            close(zz, 1.0, where + ".ZZ ideal")
            close(fidelity, 1.0, where + ".fidelity ideal")

    resource_headers, resources = read_csv("processor_resources.csv")
    require(len(resources) == 3, f"processor_resources.csv should have A/B/D rows, got {len(resources)}")
    resource_by_processor = {r["processor"]: r for r in resources}
    require(set(resource_by_processor) == {"Processor A", "Processor B", "Processor D"}, "resource rows do not cover A/B/D")
    for processor in resource_by_processor:
        row = result_by_key[(processor, "noisy", 2.0)]
        resource = resource_by_processor[processor]
        for result_field, resource_field in (("logical_qubits","logical_qubits"),("physical_qubits","physical_qubits"),
                                             ("logical_cx","logical_cx"),("cx","cx"),("depth","depth"),
                                             ("two_q_depth","two_q_depth"),("swaps","swaps"),("cx_overhead","cx_overhead")):
            close(number(row, result_field, processor + " result"), number(resource, resource_field, processor + " resource"),
                  processor + "." + result_field)

    trials_headers, trials = read_csv("lambda_optimization_trials.csv")
    require(len(trials) == 30, f"lambda_optimization_trials.csv should have 30 starts (6 lambdas × 5 seeds), got {len(trials)}")
    trial_counts: dict[float, set[int]] = {}
    for trial in trials:
        lam = number(trial, "lambda", "optimization trial")
        seed = int(number(trial, "seed", "optimization trial"))
        trial_counts.setdefault(lam, set()).add(seed)
        evals = number(trial, "objective_evaluations", "optimization trial")
        require(1 <= evals <= 200, f"COBYLA evaluations violate the 200-evaluation budget at λ={lam:g}, seed={seed}")
    require(set(trial_counts) == set(LAMBDA_VALUES), "optimizer trials do not cover the exact six required lambda values")
    for lam in LAMBDA_VALUES:
        require(trial_counts[lam] == {0,1,2,3,4}, f"optimizer trial seeds incomplete at lambda={lam:g}: {trial_counts[lam]}")

    b_noisy = result_by_key[("Processor B", "noisy", 2.0)]
    b_valid = number(b_noisy, "valid_solution_frequency", "Processor B noisy reference row")
    b_ratio = number(b_noisy, "objective_ratio_selected_valid", "Processor B noisy reference row")
    scaled_valid = min(1.0, max(0.0, (b_valid - 0.375) / (0.599 - 0.375)))
    scaled_ratio = min(1.0, max(0.0, (b_ratio - 0.474) / (1.0 - 0.474)))
    formula_points = 3.0 * scaled_valid + 3.0 * scaled_ratio

    print("RESULT CONTRACT: PASS")
    print("- Organizer's required 18 result columns preserved in order; PS-O2 metric extensions explicit")
    print("- quality_value is valid-solution frequency; objective ratio is independently reported")
    print(f"- Processor B noisy Objective-3 formula inputs: valid={b_valid:.6f}, ratio={b_ratio:.6f}; formula component={formula_points:.2f}/6 (not a judge score)")
    print("- 16 required A/B/D × condition × lambda rows verified")
    print("- 4 Bell rows and fidelity/standard-error formula verified")
    print("- 12 D penalty rows, exact ground-state feasibility transition and all 30 optimizer starts verified")
    print("- Results, details, and resource metrics agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
