#!/usr/bin/env python3
"""Run the complete official PS-O2 Processor A/B/D benchmark and lambda sweep.

This script modifies only generated results under results/ and generated result
sections inside README.md/report.md. It never modifies organizer source files.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import sys
import time
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
EVIDENCE = RESULTS / "evidence" / "processor_d_sweep"
EXPECTED_SHA256 = {
    "qff_phase2.py": "04be4fa610ba60854a2b3b9237891df7e8ade62e2fcd9659076e36e794f077ab",
    "data/instances.json": "9b5738e6c6c13208599c63aae97ec0549bf993c810bcda278ff8795a684ad09d",
}
PROTECTED_FILES = [
    "qff_phase2.py", "data/instances.json", "data/instance.json",
    "processors/processor_A.json", "processors/processor_B.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            clean = {}
            for key, value in row.items():
                if isinstance(value, bool):
                    value = "true" if value else "false"
                elif isinstance(value, (tuple, list, dict)):
                    value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
                clean[key] = value
            writer.writerow(clean)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], precision: int = 4) -> str:
    lines = ["| " + " | ".join(label for _, label in columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = f"{value:.{precision}f}" if math.isfinite(value) else ""
            if isinstance(value, (list, tuple)):
                value = ", ".join(map(str, value))
            cells.append(str(value).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def find_candidate_distances(processor: dict, qff) -> tuple[tuple[int, int], tuple[int, int], int]:
    edges = sorted(tuple(sorted(map(int, e))) for e in processor["edges"])
    adjacent = edges[0]
    cmap = qff.coupling_map_from_edges(processor["edges"], processor["num_qubits"])
    pairs = list(itertools.combinations(range(processor["num_qubits"]), 2))
    distances = [(int(cmap.distance(a, b)), (a, b)) for a, b in pairs]
    diameter = max(d for d, _ in distances)
    farthest = min(pair for d, pair in distances if d == diameter)
    return adjacent, farthest, diameter


def bitstring_x(x: tuple[int, ...]) -> str:
    return "".join(str(int(v)) for v in x)


def output_counts(qff, circuit, processor: dict, noisy: bool, shots: int) -> Counter[tuple[int, ...]]:
    compiled = qff.transpile_for(circuit, processor)
    sim = qff.simulator(noisy=noisy, processor=processor)
    counts = sim.run(compiled, shots=shots).result().get_counts()
    if sum(int(v) for v in counts.values()) != shots:
        raise RuntimeError(f"Expected exactly {shots} shots, got {sum(counts.values())}")
    result: Counter[tuple[int, ...]] = Counter()
    for key, count in counts.items():
        x = tuple(qff.counts_to_x(key))
        if len(x) != 4:
            raise RuntimeError(f"Unexpected measured bitstring width {len(x)} for {key!r}")
        result[x] += int(count)
    return result


def evaluate_counts(counts: Counter[tuple[int, ...]], shots: int, states: list[tuple[int, ...]],
                    f_values: dict[tuple[int, ...], float], k: int, opt_states: set[tuple[int, ...]],
                    F_star: float) -> dict[str, Any]:
    valid_counts = [(x, n) for x, n in counts.items() if sum(x) == k and n > 0]
    valid_shots = sum(n for x, n in counts.items() if sum(x) == k)
    opt_shots = sum(n for x, n in counts.items() if x in opt_states)
    feasible_objective_sum = sum(n * f_values[x] for x, n in counts.items() if sum(x) == k)
    if valid_counts:
        selected_x, selected_n = sorted(valid_counts, key=lambda item: (-item[1], bitstring_x(item[0])))[0]
        selected = bitstring_x(selected_x)
        selected_F = float(f_values[selected_x])
        selected_assets = [i for i, bit in enumerate(selected_x) if bit]
        selected_ratio = selected_F / F_star
        mean_valid = feasible_objective_sum / valid_shots
    else:
        selected, selected_n, selected_F, selected_assets, selected_ratio, mean_valid = "", 0, "", [], "", ""
    return {
        "selected_portfolio_x0_to_x3": selected,
        "selected_asset_indices": selected_assets,
        "selected_portfolio_shots": selected_n,
        "selected_F": selected_F,
        "best_sampled_valid_portfolio_x0_to_x3": max(
            (bitstring_x(x) for x, n in counts.items() if sum(x) == k and n > 0),
            key=lambda s: (f_values[tuple(int(c) for c in s)], s), default=""
        ),
        "valid_solution_frequency": valid_shots / shots,
        "p_opt": opt_shots / shots,
        "mean_F_valid_samples": mean_valid,
        "feasible_objective_yield": feasible_objective_sum / (shots * F_star),
        "objective_ratio_selected_valid": selected_ratio,
        "classical_optimum_F_star": F_star,
        "shots": shots,
    }


def make_figures(condition_rows: list[dict], lambda_rows: list[dict], processor: dict,
                 sweep_summary: list[dict]) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    # A/B/D primary quality comparison at reference lambda.
    base_rows = [r for r in condition_rows if float(r["lambda"]) == 2.0]
    processors = ["Processor A", "Processor B", "Processor D"]
    conditions = ["ideal", "noisy"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    x = np.arange(len(processors))
    width = 0.34
    for j, cond in enumerate(conditions):
        by_name = {r["processor"]: r for r in base_rows if r["condition"] == cond}
        vals = [float(by_name[p]["valid_solution_frequency"]) for p in processors]
        axes[0].bar(x + (j - 0.5) * width, vals, width, label=cond.title())
        pvals = [float(by_name[p]["p_opt"]) for p in processors]
        axes[1].bar(x + (j - 0.5) * width, pvals, width, label=cond.title())
    axes[0].set_title("Valid-portfolio frequency")
    axes[1].set_title("Optimal-portfolio probability")
    for ax in axes:
        ax.set_xticks(x, processors)
        ax.set_ylim(0, max(ax.get_ylim()[1], 0.55))
        ax.grid(axis="y", alpha=0.25)
        ax.legend(frameon=False)
    axes[0].set_ylabel("Fraction of 4,096 shots")
    axes[1].set_ylabel("Fraction of 4,096 shots")
    fig.suptitle("PS-O2 at reference penalty λ = 2", fontweight="bold")
    fig.savefig(FIGURES / "processor_comparison_ps_o2.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # D1 topology diagram.
    G = nx.Graph()
    G.add_nodes_from(range(int(processor["num_qubits"])))
    G.add_edges_from([tuple(e) for e in processor["edges"]])
    pos = {0:(0,0),1:(1,1),2:(1,-1),3:(-1,1),4:(-1,-1),5:(-2,-1.8)}
    fig, ax = plt.subplots(figsize=(7, 5.2))
    nx.draw_networkx_edges(G, pos, width=2.2, edge_color="#315C8C", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=1100, node_color=["#E5EEF8"]*4+["#FCE9E7"]*2,
                           edgecolors="#24496E", linewidths=1.7, ax=ax)
    nx.draw_networkx_labels(G, pos, labels={n:f"q{n}" for n in G.nodes}, font_size=11, font_weight="bold", ax=ax)
    ax.set_title("Processor D1 — K4 asset core + two-edge tail", fontsize=13, fontweight="bold")
    ax.text(0.5, -0.14, "K4 core directly connects all six pairwise asset interactions",
            transform=ax.transAxes, ha="center", fontsize=9)
    ax.axis("off")
    fig.savefig(FIGURES / "processor_d_topology.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Lambda penalty sensitivity.
    sweep_lams = sorted({float(r["lambda"]) for r in lambda_rows})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for cond in conditions:
        rows = sorted([r for r in lambda_rows if r["condition"] == cond], key=lambda r: float(r["lambda"]))
        axes[0].plot([float(r["lambda"]) for r in rows],
                     [float(r["valid_solution_frequency"]) for r in rows],
                     marker="o", linewidth=2, label=cond.title())
        axes[1].plot([float(r["lambda"]) for r in rows],
                     [float(r["p_opt"]) for r in rows],
                     marker="o", linewidth=2, label=f"P(opt), {cond}")
        axes[1].plot([float(r["lambda"]) for r in rows],
                     [float(r["objective_ratio_selected_valid"] or 0) for r in rows],
                     marker="s", linestyle="--", linewidth=1.5, label=f"Selected ratio, {cond}")
    axes[0].set_title("Valid-solution frequency")
    axes[1].set_title("Optimal sampling and selected objective ratio")
    axes[0].set_xlabel("Penalty λ")
    axes[1].set_xlabel("Penalty λ")
    axes[0].set_ylabel("Fraction of shots")
    axes[1].set_ylabel("Fraction / ratio")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Processor D1 penalty sensitivity (angles re-optimized per λ)", fontweight="bold")
    fig.savefig(FIGURES / "processor_d_lambda_sweep.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def replace_generated_section(path: Path, start: str, end: str, generated: str) -> None:
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + start + "\n\n" + generated.rstrip() + "\n\n" + end + after, encoding="utf-8")


def main() -> int:
    start_time = time.perf_counter()
    for rel, expected in EXPECTED_SHA256.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            raise RuntimeError(f"Official source hash mismatch: {rel}: expected {expected}, got {actual}")
        print(f"PASS official source hash: {rel}")

    before = {rel: sha256(ROOT / rel) for rel in PROTECTED_FILES}
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    import qff_phase2 as qff
    from src.classical_reference import enumerate_reference, load_instance, objective
    from src.qaoa_circuit import build_qaoa_p1_circuit, optimize_qaoa_restarts

    if qff.SHOTS != 4096 or qff.SEED != 42 or qff.BASIS_GATES != ["rz", "sx", "x", "cx"]:
        raise RuntimeError("Official qff_phase2 benchmark settings differ from required settings")
    if qff.OPT_LEVEL != 1:
        raise RuntimeError("Official transpiler optimization level changed; aborting.")

    instance = load_instance(ROOT / "data/instance.json")
    locked = json.loads((ROOT / "data/instances.json").read_text(encoding="utf-8"))["PS-O2"]
    for key in ("expected_returns", "risk_matrix", "risk_aversion_q", "k", "required_lambda_sweep"):
        if instance.get(key) != locked.get(key):
            raise RuntimeError(f"Derived PS-O2 instance mismatches official {key}")

    D_path = ROOT / "processors/processor_D.json"
    D_doc = json.loads(D_path.read_text(encoding="utf-8"))
    D = qff.load_processor(str(D_path))
    if D_doc.get("selection_status") != "selected":
        # selection_status is optional in organizer schema but intentionally used here to reject stale D.
        raise RuntimeError("Processor D is not explicitly marked selected by the finalization payload")
    violations = qff.validate_processor_d(D, required_qubits=4)
    if violations:
        raise RuntimeError(f"Official Processor D validation failed: {violations}")
    if D["num_qubits"] != 6 or sorted(tuple(sorted(e)) for e in D["edges"]) != sorted(
        [(0,1),(0,2),(0,3),(0,4),(1,2),(1,3),(2,3),(4,5)]
    ):
        raise RuntimeError("processors/processor_D.json is not the selected D1 K4-tail topology")

    ref = enumerate_reference(instance)
    F_star = float(ref["classical_optimum_F_star"])
    n = len(instance["expected_returns"])
    states = [tuple((mask >> i) & 1 for i in range(n)) for mask in range(1 << n)]
    mu = np.asarray(instance["expected_returns"], dtype=float)
    sigma = np.asarray(instance["risk_matrix"], dtype=float)
    q = float(instance["risk_aversion_q"])
    k = int(instance["k"])
    f_values = {x: float(objective(x, mu, sigma, q)) for x in states}
    optimal_states = {tuple(int(c) for c in row["bitstring_x0_to_xn"]) for row in ref["optimal_portfolios"]}
    random_baseline_ratio = float(ref["uniform_random_baseline"]["mean_valid_objective_ratio"])

    # Re-optimize λ=2 from all five required seeds; reuse the winning angles across A/B/D.
    lambda_values = [float(v) for v in instance["required_lambda_sweep"]]
    trials_all = []
    best_by_lambda: dict[float, dict[str, Any]] = {}
    for lam in lambda_values:
        trials = optimize_qaoa_restarts(instance, penalty=lam, seeds=(0,1,2,3,4), max_function_evaluations=200)
        for r in trials:
            row = dict(r)
            row["lambda"] = lam
            trials_all.append(row)
        # Minimum exact expected energy; ties break by seed.
        best = sorted(trials, key=lambda r: (float(r["expected_qubo_energy"]), int(r["seed"])))[0]
        best_by_lambda[lam] = best
        print(f"Optimization λ={lam:g}: selected seed={best['seed']} E={best['expected_qubo_energy']:.8f} "
              f"gamma={best['gamma']:.8f} beta={best['beta']:.8f}")
    ref_best = best_by_lambda[2.0]
    gamma, beta = float(ref_best["gamma"]), float(ref_best["beta"])
    print(f"Reference λ=2 angles: gamma={gamma:.12f}, beta={beta:.12f}")

    processors = [
        {"name": "Processor A", "num_qubits": qff.PROCESSOR_A["num_qubits"], "edges": list(qff.PROCESSOR_A["edges"])},
        {"name": "Processor B", "num_qubits": qff.PROCESSOR_B["num_qubits"], "edges": list(qff.PROCESSOR_B["edges"])},
        D,
    ]
    condition_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    resource_rows: list[dict[str, Any]] = []
    for p in processors:
        p_name = p["name"]
        logical = build_qaoa_p1_circuit(instance, 2.0, gamma, beta, measure=True)
        resources = qff.circuit_metrics(logical, p)
        if not resources.get("executable", False):
            raise RuntimeError(f"PS-O2 should fit {p_name}; got {resources}")
        resource_rows.append({"problem_id":"PS-O2", **resources})
        for condition in ("ideal", "noisy"):
            counts = output_counts(qff, logical, p, condition == "noisy", qff.SHOTS)
            metrics = evaluate_counts(counts, qff.SHOTS, states, f_values, k, optimal_states, F_star)
            row = {
                "lambda": 2.0, "problem_id":"PS-O2", "processor":p_name,
                "condition":condition, "executable":True,
                "logical_qubits":resources["logical_qubits"], "physical_qubits":resources["physical_qubits"],
                "logical_cx":resources["logical_cx"], "cx":resources["cx"], "depth":resources["depth"],
                "two_q_depth":resources["two_q_depth"], "swaps":resources["swaps"], "cx_overhead":resources["cx_overhead"],
                "shots":qff.SHOTS, "quality_metric":"objective_ratio_selected_valid",
                "quality_value":metrics["objective_ratio_selected_valid"], "p_opt":metrics["p_opt"],
                "classical_optimum":F_star, "random_baseline":random_baseline_ratio,
                "gamma":gamma, "beta":beta,
                "random_baseline_valid_frequency":float(ref["uniform_random_baseline"]["valid_frequency"]),
                "random_baseline_p_opt":float(ref["uniform_random_baseline"]["p_opt"]),
                "random_baseline_objective_ratio":random_baseline_ratio,
                **metrics,
            }
            condition_rows.append(row)
            result_rows.append({k0: row.get(k0, "") for k0 in [
                "problem_id","processor","condition","executable","logical_qubits","physical_qubits",
                "logical_cx","cx","depth","two_q_depth","swaps","cx_overhead","shots",
                "quality_metric","quality_value","p_opt","classical_optimum","random_baseline","lambda"
            ]})
            print(f"{p_name} {condition}: valid={metrics['valid_solution_frequency']:.6f} "
                  f"P_opt={metrics['p_opt']:.6f} selected={metrics['selected_portfolio_x0_to_x3']} "
                  f"F={metrics['selected_F']} CX={resources['cx']} depth={resources['depth']}")

    # Required D Bell experiments: one adjacent physical pair and one farthest pair.
    adjacent, farthest, diameter = find_candidate_distances(D, qff)
    bell_rows = []
    for pair_type, pair in (("adjacent", adjacent), ("farthest", farthest)):
        for condition in ("ideal", "noisy"):
            outcome = qff.bell_experiment(D, physical_pair=pair, noisy=(condition == "noisy"), shots=qff.SHOTS)
            bell_rows.append({
                "problem_id":"PS-O2", "processor":"Processor D", "pair_type":pair_type,
                "physical_pair":json.dumps(list(pair)), "pair_distance":int(outcome["pair_distance"]),
                "condition":condition, "shots":qff.SHOTS, "cx":outcome.get("cx",""),
                "XX":outcome["XX"], "XX_se":outcome["XX_se"],
                "YY":outcome["YY"], "YY_se":outcome["YY_se"],
                "ZZ":outcome["ZZ"], "ZZ_se":outcome["ZZ_se"],
                "fidelity":outcome["fidelity"], "fidelity_se":outcome["fidelity_se"],
            })
            print(f"Bell {pair_type} pair={pair} {condition}: F={outcome['fidelity']:.6f} +/- {outcome['fidelity_se']:.6f}")

    # Required full λ sweep on D; angles are independently re-optimized per λ.
    lambda_rows: list[dict[str, Any]] = []
    for lam in lambda_values:
        best = best_by_lambda[lam]
        logical = build_qaoa_p1_circuit(instance, lam, float(best["gamma"]), float(best["beta"]), measure=True)
        exact_sweep_row = next(r for r in ref["exact_penalty_sweep"] if float(r["lambda"]) == lam)
        for condition in ("ideal", "noisy"):
            counts = output_counts(qff, logical, D, condition == "noisy", qff.SHOTS)
            metrics = evaluate_counts(counts, qff.SHOTS, states, f_values, k, optimal_states, F_star)
            lamrow = {
                "problem_id":"PS-O2","processor":"Processor D","lambda":lam,"condition":condition,
                "shots":qff.SHOTS,"optimizer":"COBYLA","selected_seed":best["seed"],
                "gamma":best["gamma"],"beta":best["beta"],"expected_qubo_energy":best["expected_qubo_energy"],
                "qubo_minimum_energy":exact_sweep_row["min_qubo_energy"],
                "qubo_minimum_bitstrings":";".join(exact_sweep_row["minimizing_bitstrings_x0_to_xn"]),
                "qubo_minimum_valid":exact_sweep_row["all_minima_valid"],
                "valid_solution_frequency":metrics["valid_solution_frequency"],
                "p_opt":metrics["p_opt"],
                "selected_portfolio_x0_to_x3":metrics["selected_portfolio_x0_to_x3"],
                "selected_F":metrics["selected_F"],
                "best_sampled_valid_portfolio_x0_to_x3":metrics["best_sampled_valid_portfolio_x0_to_x3"],
                "mean_F_valid_samples":metrics["mean_F_valid_samples"],
                "objective_ratio_selected_valid":metrics["objective_ratio_selected_valid"],
                "feasible_objective_yield":metrics["feasible_objective_yield"],
                "classical_optimum_F_star":F_star,
                "random_baseline_valid_frequency":float(ref["uniform_random_baseline"]["valid_frequency"]),
                "random_baseline_p_opt":float(ref["uniform_random_baseline"]["p_opt"]),
                "random_baseline_objective_ratio":random_baseline_ratio,
            }
            lambda_rows.append(lamrow)
            # Results.csv has one row per processor x condition x lambda for PS-O2.
            # Reference-penalty A/B rows are already present above; include D for non-reference lambdas here.
            if lam != 2.0:
                resources = qff.circuit_metrics(logical, D)
                result_rows.append({
                    "problem_id":"PS-O2","processor":"Processor D","condition":condition,"executable":True,
                    "logical_qubits":resources["logical_qubits"],"physical_qubits":resources["physical_qubits"],
                    "logical_cx":resources["logical_cx"],"cx":resources["cx"],"depth":resources["depth"],
                    "two_q_depth":resources["two_q_depth"],"swaps":resources["swaps"],"cx_overhead":resources["cx_overhead"],
                    "shots":qff.SHOTS,"quality_metric":"objective_ratio_selected_valid",
                    "quality_value":metrics["objective_ratio_selected_valid"],"p_opt":metrics["p_opt"],
                    "classical_optimum":F_star,"random_baseline":random_baseline_ratio,"lambda":lam,
                })
            print(f"D λ={lam:g} {condition}: QUBO-min-valid={exact_sweep_row['all_minima_valid']} "
                  f"valid={metrics['valid_solution_frequency']:.6f} P_opt={metrics['p_opt']:.6f} "
                  f"ratio={metrics['objective_ratio_selected_valid']}")

    # Persist official-schema files, detail tables and reproducibility metadata.
    TABLES.mkdir(parents=True, exist_ok=True)
    write_csv(TABLES / "results.csv", result_rows, [
        "problem_id","processor","condition","executable","logical_qubits","physical_qubits",
        "logical_cx","cx","depth","two_q_depth","swaps","cx_overhead","shots",
        "quality_metric","quality_value","p_opt","classical_optimum","random_baseline","lambda"
    ])
    write_csv(TABLES / "bell.csv", bell_rows)
    write_csv(TABLES / "processor_conditions.csv", condition_rows)
    write_csv(TABLES / "processor_resources.csv", resource_rows)
    write_csv(TABLES / "processor_d_lambda_sweep.csv", lambda_rows)
    write_csv(TABLES / "lambda_optimization_trials.csv", trials_all)
    write_csv(TABLES / "classical_solutions.csv", ref["all_valid_portfolios"])
    Q = ref["qubo_matrix_lambda_2"]
    write_csv(TABLES / "qubo_matrix_lambda_2.csv", [
        {"row": i, **{f"Q{j}": Q[i][j] for j in range(len(Q))}} for i in range(len(Q))
    ])

    make_figures(condition_rows, lambda_rows, D, ref["exact_penalty_sweep"])

    # Archive the three-candidate selection report and raw sweep outputs, if available.
    tmp_results = ROOT / "tmp/processor_d_sweep/results"
    if tmp_results.is_dir():
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        for name in ("summary.md", "candidate_conditions.csv", "candidate_resources.csv",
                     "candidate_bell.csv", "candidate_ranking.csv", "run_metadata.json",
                     "recommendation_metadata.json"):
            src = tmp_results / name
            if src.is_file():
                shutil_target = EVIDENCE / name
                shutil_target.write_bytes(src.read_bytes())

    selected_metrics = next(r for r in condition_rows if r["processor"] == "Processor D" and r["condition"] == "noisy")
    base_table = markdown_table(condition_rows, [
        ("processor","Processor"),("condition","Condition"),("selected_portfolio_x0_to_x3","Selected"),
        ("selected_F","Selected F"),("classical_optimum_F_star","F*"),
        ("objective_ratio_selected_valid","Objective ratio"),("valid_solution_frequency","Valid frequency"),
        ("p_opt","P(opt)"),("random_baseline_valid_frequency","Random valid"),
        ("random_baseline_p_opt","Random P(opt)"),("random_baseline_objective_ratio","Random objective ratio"),
    ])
    resource_table = markdown_table(resource_rows, [
        ("processor","Processor"),("logical_qubits","Logical qubits"),("physical_qubits","Physical qubits"),
        ("logical_cx","Logical CX"),("cx","Compiled CX"),("depth","Depth"),
        ("two_q_depth","Two-qubit depth"),("swaps","SWAPs"),("cx_overhead","CX overhead")
    ])
    valid_portfolio_table = markdown_table(ref["all_valid_portfolios"], [
        ("bitstring_x0_to_xn","Portfolio x0…x3"),("selected_indices","Selected assets"),
        ("selected_count","Asset count"),("F","F(x)")
    ])
    Q = ref["qubo_matrix_lambda_2"]
    Q_rows = [
        {"row":f"x{i}", **{f"x{j}":float(Q[i][j]) for j in range(len(Q))}}
        for i in range(len(Q))
    ]
    qubo_table = markdown_table(Q_rows, [("row","Row"),("x0","x0"),("x1","x1"),("x2","x2"),("x3","x3")], precision=4)
    lambda_table = markdown_table(lambda_rows, [
        ("lambda","λ"),("condition","Condition"),("qubo_minimum_valid","QUBO minimum valid"),
        ("valid_solution_frequency","Valid frequency"),("p_opt","P(opt)"),
        ("selected_portfolio_x0_to_x3","Selected"),("objective_ratio_selected_valid","Objective ratio"),
        ("selected_seed","Seed"),("gamma","γ"),("beta","β")
    ])
    bell_table = markdown_table(bell_rows, [
        ("pair_type","Pair"),("physical_pair","Physical qubits"),("condition","Condition"),
        ("pair_distance","Distance"),("XX","XX"),("YY","YY"),("ZZ","ZZ"),
        ("fidelity","Fidelity"),("fidelity_se","Fidelity SE")
    ])
    readme_table = markdown_table(condition_rows, [
        ("processor","Processor"),("condition","Condition"),("selected_portfolio_x0_to_x3","Selected"),
        ("selected_F","F"),("objective_ratio_selected_valid","Ratio"),("valid_solution_frequency","Valid"),
        ("p_opt","P(opt)"),("cx","CX"),("depth","Depth"),("swaps","SWAPs")
    ])
    readme_generated = (
        "### Reference penalty (λ = 2)\n\n" + readme_table +
        "\n\n### Selected Processor D\n\n" +
        f"- **Architecture:** D1, six-qubit K4 core plus two-edge tail; eight couplers.\n" +
        f"- **Noisy valid-solution frequency:** {selected_metrics['valid_solution_frequency']:.4%}.\n" +
        f"- **Noisy optimal-portfolio probability:** {selected_metrics['p_opt']:.4%}.\n" +
        f"- **Compiled CX / depth / SWAPs:** {selected_metrics['cx']} / {selected_metrics['depth']} / {selected_metrics['swaps']}.\n" +
        "- Processor D is selected based on the measured three-candidate sweep and the stated deterministic ranking rule. The small Bell-fidelity differences are not treated as statistically significant."
    )
    report_generated = (
        "### Six feasible portfolios and objective values\n\n" + valid_portfolio_table +
        "\n\n### QUBO matrix at λ = 2\n\n" +
        "Rows and columns use asset order x0…x3. The constant offset is retained by the classical reference helper; " +
        "the matrix is saved in `results/tables/qubo_matrix_lambda_2.csv`.\n\n" + qubo_table +
        "\n\n### Processor A/B/D at λ = 2\n\n" + base_table +
        "\n\n### Compiled resource comparison\n\n" + resource_table +
        "\n\n### Processor D Bell-state verification\n\n" + bell_table +
        "\n\n### Processor D penalty sensitivity (angles re-optimized for each λ)\n\n" + lambda_table +
        "\n\n![A/B/D quality metrics](results/figures/processor_comparison_ps_o2.png)\n\n" +
        "![Processor D topology](results/figures/processor_d_topology.png)\n\n" +
        "![Processor D penalty sweep](results/figures/processor_d_lambda_sweep.png)\n"
    )
    replace_generated_section(ROOT / "README.md", "<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->", readme_generated)
    replace_generated_section(ROOT / "report.md", "<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->", report_generated)

    metadata = {
        "status":"FINAL_PS_O2_RUN",
        "selected_processor_D":"D1_K4_TAIL_6Q",
        "processor_D_path":"processors/processor_D.json",
        "problem_id":"PS-O2",
        "lambda_reference":2.0,
        "lambda_sweep":lambda_values,
        "initialization_seeds":[0,1,2,3,4],
        "optimizer":"COBYLA",
        "max_objective_evaluations_per_start":200,
        "angle_selection":"minimum exact expected QUBO energy; tie-break by initialization seed",
        "selected_reference_seed":int(ref_best["seed"]),
        "gamma":gamma,"beta":beta,
        "shots":qff.SHOTS,"transpiler_seed":qff.SEED,"simulator_seed":qff.SEED,
        "basis_gates":qff.BASIS_GATES,"optimization_level":qff.OPT_LEVEL,
        "p1_depolarizing":qff.P1_DEPOL,"p2_depolarizing_cx":qff.P2_DEPOL,"readout_probability":qff.P_READOUT,
        "official_source_sha256":{rel:sha256(ROOT/rel) for rel in EXPECTED_SHA256},
        "runtime_seconds":time.perf_counter()-start_time,
        "no_quantum_advantage_claim":True,
        "ai_assistance_disclosed_in_readme":True,
    }
    write_json(RESULTS / "run_metadata_final.json", metadata)

    # Ensure the required source files remain byte-for-byte unchanged.
    after = {rel: sha256(ROOT / rel) for rel in PROTECTED_FILES}
    changed = [rel for rel in PROTECTED_FILES if before[rel] != after[rel]]
    if changed:
        raise RuntimeError(f"Protected official/locked inputs were changed: {changed}")

    print("\n========== FINAL PS-O2 BENCHMARK COMPLETE ==========")
    print(f"Rows in official results.csv: {len(result_rows)}")
    print(f"Bell rows: {len(bell_rows)}")
    print(f"Processor D: D1 K4 tail; selected by three-candidate benchmark")
    print(f"Report: {ROOT/'report.md'}")
    print(f"Results: {TABLES/'results.csv'}")
    print("PASS: official source/data/Processor A/B files remain byte-for-byte unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
