#!/usr/bin/env python3
"""Controlled QFF O2 routing experiment: fixed baseline vs SABRE variants.

Run from the project root after `python main.py` has generated the QAOA parameters:
    python routing_experiment.py

This leaves the original baseline files in results/ untouched and writes new files
under results/routing_experiment/. Uses the same problem instance and fixed QAOA
parameters for every processor/compiler configuration. All simulations are ideal Aer.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import transpile
from qiskit.transpiler import CouplingMap
from qiskit_aer import AerSimulator

from src.portfolio_model import (
    enumerate_solutions,
    load_instance,
    utility,
)
from src.qaoa import build_qaoa_circuit, prepare_cost_model

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "portfolio_instance.json"
PROCESSOR_DIR = ROOT / "processors"
RESULTS_DIR = ROOT / "results"
OUT_DIR = RESULTS_DIR / "routing_experiment"

# Compare routing/layout methods with the same optimization level.
STRATEGIES = [
    ("baseline_trivial_basic", "trivial", "basic"),
    ("trivial_sabre", "trivial", "sabre"),
    ("sabre_layout_sabre_route", "sabre", "sabre"),
]
REPEATS = 5
OPTIMIZATION_LEVEL = 0
BASE_SEED = 2026


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_coupling_map(processor: dict[str, Any]) -> CouplingMap:
    directed: list[tuple[int, int]] = []
    for u, v in processor["coupling_edges_undirected"]:
        directed.extend([(int(u), int(v)), (int(v), int(u))])
    coupling = CouplingMap(couplinglist=directed)
    expected = int(processor["num_qubits"])
    if coupling.size() != expected:
        raise ValueError(
            f"{processor['name']} topology has {coupling.size()} qubits, expected {expected}."
        )
    return coupling


def swap_diagnostic(
    logical_circuit,
    processor: dict[str, Any],
    layout_method: str,
    routing_method: str,
    seed: int,
) -> int:
    """Count router-inserted SWAPs before translating SWAPs into native CX gates.

    Adding `swap` only to this diagnostic basis keeps routed SWAP operations visible;
    the actual execution circuit below is compiled into the processor's real basis.
    """
    diagnostic_basis = list(processor["basis_gates"])
    if "swap" not in diagnostic_basis:
        diagnostic_basis.append("swap")
    diagnostic = transpile(
        logical_circuit,
        coupling_map=make_coupling_map(processor),
        basis_gates=diagnostic_basis,
        layout_method=layout_method,
        routing_method=routing_method,
        optimization_level=OPTIMIZATION_LEVEL,
        seed_transpiler=seed,
    )
    return int(diagnostic.count_ops().get("swap", 0))


def evaluate_counts(
    counts: dict[str, int],
    instance: dict[str, Any],
    exact_optimum: dict[str, Any],
) -> dict[str, Any]:
    n = len(instance["assets"])
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    risk_weight = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    total_shots = sum(counts.values())
    valid_count = 0
    optimal_count = 0
    weighted_utility = 0.0
    valid_weighted_utility = 0.0
    best_valid: dict[str, Any] | None = None

    for raw_key, count in counts.items():
        bitstring = raw_key.replace(" ", "")
        if len(bitstring) < n:
            bitstring = bitstring.zfill(n)
        # Qiskit count strings display the highest classical bit on the left.
        x = np.asarray([int(bitstring[-1 - i]) for i in range(n)], dtype=int)
        is_valid = int(x.sum()) == k
        score = utility(x, returns, risk, risk_weight)
        weighted_utility += (count / total_shots) * score
        if is_valid:
            valid_count += count
            valid_weighted_utility += count * score
            if bitstring[-n:] == exact_optimum["bitstring"]:
                optimal_count += count
            candidate = {
                "bitstring": bitstring[-n:],
                "utility": float(score),
                "count": int(count),
                "probability": float(count / total_shots),
                "selected_assets": [instance["assets"][i] for i, bit in enumerate(x) if bit],
            }
            if best_valid is None or candidate["utility"] > best_valid["utility"]:
                best_valid = candidate

    exact_utility = float(exact_optimum["utility"])
    best_utility = None if best_valid is None else float(best_valid["utility"])
    ratio = None
    if best_utility is not None and exact_utility > 1e-12 and best_utility >= 0:
        ratio = best_utility / exact_utility
    return {
        "valid_portfolio_probability": valid_count / total_shots,
        "optimal_portfolio_probability": optimal_count / total_shots,
        "sampled_expected_utility_all_outcomes": weighted_utility,
        "sampled_expected_utility_given_valid": (
            valid_weighted_utility / valid_count if valid_count else None
        ),
        "best_sampled_valid_utility": best_utility,
        "optimality_gap": None if best_utility is None else exact_utility - best_utility,
        "best_sampled_objective_ratio": ratio,
        "best_sampled_bitstring": None if best_valid is None else best_valid["bitstring"],
    }


def compile_metrics(compiled, processor: dict[str, Any]) -> dict[str, Any]:
    counts = compiled.count_ops()
    active = {
        compiled.find_bit(qubit).index
        for instruction in compiled.data
        for qubit in instruction.qubits
    }
    return {
        "processor_qubits": int(processor["num_qubits"]),
        "compiled_qubits": int(compiled.num_qubits),
        "physical_qubits_touched": len(active),
        "depth": int(compiled.depth()),
        "cx_count": int(counts.get("cx", 0)),
        "h_count": int(counts.get("h", 0)),
        "rz_count": int(counts.get("rz", 0)),
        "sx_count": int(counts.get("sx", 0)),
        "x_count": int(counts.get("x", 0)),
    }


def plot_summary(rows: list[dict[str, Any]]) -> None:
    processors = ["Processor A", "Processor B"]
    strategies = [item[0] for item in STRATEGIES]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, metric, title, ylabel in [
        (axes[0], "cx_count", "CX gate count", "CX gates (lower is better)"),
        (axes[1], "depth", "Circuit depth", "Depth (lower is better)"),
    ]:
        for proc in processors:
            medians = []
            for strategy in strategies:
                values = [
                    float(row[metric]) for row in rows
                    if row["processor"] == proc and row["strategy"] == strategy
                ]
                medians.append(statistics.median(values) if values else float("nan"))
            ax.plot(strategies, medians, marker="o", label=proc)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", labelrotation=25)
        ax.grid(axis="y", alpha=0.3)
        ax.legend()
    fig.suptitle("Portfolio QAOA routing experiment (median across compiler seeds)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "routing_resource_comparison.png", dpi=180)
    plt.close(fig)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    params_path = RESULTS_DIR / "qaoa_parameters.json"
    metadata_path = RESULTS_DIR / "run_metadata.json"
    if not params_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Run `python main.py` successfully before routing_experiment.py.")

    instance = load_instance(DATA_PATH)
    parameters = read_json(params_path)
    metadata = read_json(metadata_path)
    penalty = float(metadata["penalty_weight"])
    cost_model = prepare_cost_model(instance, penalty)
    logical_circuit = build_qaoa_circuit(
        gamma=float(parameters["gamma"]),
        beta=float(parameters["beta"]),
        cost_model=cost_model,
        measured=True,
    )

    solutions = enumerate_solutions(instance, penalty)
    feasible = [item for item in solutions if item["feasible"]]
    exact_optimum = max(feasible, key=lambda item: item["utility"])
    processors = [read_json(PROCESSOR_DIR / "processor_A.json"), read_json(PROCESSOR_DIR / "processor_B.json")]
    simulator = AerSimulator()
    rows: list[dict[str, Any]] = []
    total = len(processors) * len(STRATEGIES) * REPEATS
    finished = 0

    print("Routing experiment: same logical circuit, same QAOA parameters, same optimization level.")
    print(f"Instance status: {instance.get('source_status', 'UNLABELLED')}")
    print(f"Exact classical optimum: {exact_optimum['selected_assets']} (utility={exact_optimum['utility']:.6f})")
    print(f"Runs: {total} (2 processors × {len(STRATEGIES)} strategies × {REPEATS} seeds)")

    for processor_idx, processor in enumerate(processors):
        coupling = make_coupling_map(processor)
        for strategy_name, layout_method, routing_method in STRATEGIES:
            for repeat in range(REPEATS):
                # Use paired seeds across strategies for each processor/repeat to aid comparison.
                seed = BASE_SEED + repeat * 100 + processor_idx
                started = time.perf_counter()
                compiled = transpile(
                    logical_circuit,
                    coupling_map=coupling,
                    basis_gates=list(processor["basis_gates"]),
                    layout_method=layout_method,
                    routing_method=routing_method,
                    optimization_level=OPTIMIZATION_LEVEL,
                    seed_transpiler=seed,
                )
                compile_seconds = time.perf_counter() - started
                swap_count = swap_diagnostic(
                    logical_circuit, processor, layout_method, routing_method, seed
                )
                result = simulator.run(
                    compiled,
                    shots=int(instance.get("shots", 4096)),
                    seed_simulator=seed,
                ).result()
                counts = result.get_counts(compiled)
                quality = evaluate_counts(counts, instance, exact_optimum)
                row: dict[str, Any] = {
                    "processor": processor["name"],
                    "strategy": strategy_name,
                    "layout_method": layout_method,
                    "routing_method": routing_method,
                    "optimization_level": OPTIMIZATION_LEVEL,
                    "repeat": repeat,
                    "seed": seed,
                    "shots": int(instance.get("shots", 4096)),
                    "swap_count_diagnostic": swap_count,
                    "compile_seconds": compile_seconds,
                    **compile_metrics(compiled, processor),
                    **quality,
                }
                rows.append(row)
                finished += 1
                print(
                    f"[{finished:02d}/{total}] {processor['name']} / {strategy_name} / seed={seed}: "
                    f"CX={row['cx_count']}, depth={row['depth']}, swaps={swap_count}, "
                    f"valid={row['valid_portfolio_probability']:.3f}, "
                    f"optimal={row['optimal_portfolio_probability']:.3f}"
                )

    write_csv(OUT_DIR / "routing_experiment_trials.csv", rows)
    summary: list[dict[str, Any]] = []
    numeric_metrics = [
        "cx_count", "depth", "swap_count_diagnostic", "compile_seconds",
        "valid_portfolio_probability", "optimal_portfolio_probability",
        "sampled_expected_utility_all_outcomes", "sampled_expected_utility_given_valid",
    ]
    for processor in processors:
        for strategy_name, layout_method, routing_method in STRATEGIES:
            group = [
                row for row in rows
                if row["processor"] == processor["name"] and row["strategy"] == strategy_name
            ]
            item: dict[str, Any] = {
                "processor": processor["name"],
                "strategy": strategy_name,
                "layout_method": layout_method,
                "routing_method": routing_method,
                "repeats": len(group),
            }
            for metric in numeric_metrics:
                vals = [float(row[metric]) for row in group if row.get(metric) is not None]
                item[f"median_{metric}"] = statistics.median(vals) if vals else None
                item[f"min_{metric}"] = min(vals) if vals else None
                item[f"max_{metric}"] = max(vals) if vals else None
            summary.append(item)

    write_csv(OUT_DIR / "routing_experiment_summary.csv", summary)
    plot_summary(rows)

    report_lines = [
        "# Routing and placement experiment — O2 Portfolio QAOA",
        "",
        f"- Instance source status: `{instance.get('source_status', 'UNLABELLED')}`",
        f"- Fixed QAOA angles: gamma `{parameters['gamma']:.8f}`, beta `{parameters['beta']:.8f}`",
        f"- Shots per trial: `{instance.get('shots', 4096)}`",
        f"- Compiler optimization level: `{OPTIMIZATION_LEVEL}` for all strategies",
        f"- Seeds per processor/strategy: `{REPEATS}`",
        "- Simulator: ideal Aer; no hardware noise model is configured.",
        "- Problem instance and optimized QAOA angles were held fixed; only layout/routing strategy and compiler seed changed.",
        "",
        "## Median results across seeds",
        "",
        "| Processor | Strategy | Median CX | Median depth | Median SWAP diagnostic | Mean valid probability | Mean optimal probability |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        g = [r for r in rows if r["processor"] == item["processor"] and r["strategy"] == item["strategy"]]
        mean_valid = statistics.mean(float(x["valid_portfolio_probability"]) for x in g)
        mean_opt = statistics.mean(float(x["optimal_portfolio_probability"]) for x in g)
        report_lines.append(
            f"| {item['processor']} | {item['strategy']} | {item['median_cx_count']:.1f} | "
            f"{item['median_depth']:.1f} | {item['median_swap_count_diagnostic']:.1f} | "
            f"{mean_valid:.4f} | {mean_opt:.4f} |"
        )
    report_lines += [
        "",
        "## Interpretation guidance",
        "",
        "- Compare `baseline_trivial_basic` against `trivial_sabre` to assess routing-method changes with the trivial initial layout retained.",
        "- Compare `trivial_sabre` against `sabre_layout_sabre_route` to assess the additional effect of SABRE layout selection when the routing method is held at SABRE.",
        "- Read gate/depth metrics alongside valid-portfolio and optimal-portfolio probabilities; a lower gate count alone does not prove better optimization quality.",
        "- SWAP count is measured in a separate diagnostic compile that keeps SWAP gates visible. CX count and depth are measured on the native-basis compiled circuit.",
        "- The matrix is synthetic development data unless replaced and correctly labelled from an authoritative source. Do not present these results as official-instance data.",
        "- Report only observed results. Do not claim quantum advantage or noisy-device performance from this ideal, four-asset simulation.",
        "",
        "Files: `routing_experiment_trials.csv`, `routing_experiment_summary.csv`, `routing_resource_comparison.png`.",
    ]
    (OUT_DIR / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("\nRouting experiment complete.")
    print(f"Trial metrics: {OUT_DIR / 'routing_experiment_trials.csv'}")
    print(f"Summary:       {OUT_DIR / 'routing_experiment_summary.csv'}")
    print(f"Figure:        {OUT_DIR / 'routing_resource_comparison.png'}")
    print(f"Report:        {OUT_DIR / 'report.md'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Routing experiment failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
