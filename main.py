"""QFF 2026 Phase 1 — O2 Constrained Portfolio Optimization.

Run: python main.py
The current risk matrix is explicitly labelled synthetic until the organizer's
numeric matrix is confirmed. Output files are written under results/.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from src.portfolio_model import (
    choose_penalty_weight,
    enumerate_solutions,
    load_instance,
    validate_qubo_conversion,
)
from src.qaoa import optimize_qaoa, sample_processor

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "portfolio_instance.json"
PROCESSOR_DIR = ROOT / "processors"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)


def make_instance_plot(instance: dict, all_solutions: list[dict]) -> None:
    feasible = sorted((s for s in all_solutions if s["feasible"]), key=lambda s: s["utility"], reverse=True)
    labels = [" + ".join(s["selected_assets"]) for s in feasible]
    values = [s["utility"] for s in feasible]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    positions = np.arange(len(values))
    ax.bar(positions, values)
    ax.set_xticks(positions, labels, rotation=35, ha="right")
    ax.set_ylabel("Return–risk utility (higher is better)")
    ax.set_title("Exact classical baseline: feasible two-asset portfolios")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "classical_portfolio_objectives.png", dpi=180)
    plt.close(fig)


def make_coupling_plot(processor_a: dict, processor_b: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, processor in zip(axes, (processor_a, processor_b)):
        graph = nx.Graph()
        graph.add_nodes_from(range(processor["num_qubits"]))
        graph.add_edges_from(tuple(edge) for edge in processor["coupling_edges_undirected"])
        pos = nx.spring_layout(graph, seed=12)
        nx.draw_networkx(graph, pos=pos, ax=ax, node_size=520, font_size=9, width=1.5)
        ax.set_title(f"{processor['name']} ({processor['num_qubits']} qubits)")
        ax.axis("off")
    fig.suptitle("Organizer-supplied processor coupling topologies")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "processor_topologies.png", dpi=180)
    plt.close(fig)


def make_distribution_plot(samples: list[dict], processor_name: str) -> None:
    ordered = sorted(samples, key=lambda row: row["probability"], reverse=True)[:12]
    labels = [row["bitstring"] for row in ordered]
    values = [row["probability"] for row in ordered]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(labels, values)
    ax.set_xlabel("Measured bitstring (asset 4 ... asset 1)")
    ax.set_ylabel("Observed probability")
    ax.set_title(f"Most frequent QAOA outcomes — {processor_name}")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    filename = "qaoa_distribution_" + processor_name.lower().replace(" ", "_") + ".png"
    fig.savefig(FIGURES_DIR / filename, dpi=180)
    plt.close(fig)


def write_comparison_csv(rows: list[dict]) -> None:
    fields = [
        "processor", "processor_qubits", "compiled_qubits", "physical_qubits_touched",
        "shots", "depth", "cx_count", "swap_count_basic_routing",
        "valid_portfolio_probability", "optimal_portfolio_probability",
        "sampled_expected_utility_all_outcomes", "sampled_expected_utility_given_valid",
        "exact_optimal_utility", "best_sampled_valid_utility",
        "optimality_gap", "best_sampled_objective_ratio", "layout_method", "routing_method",
        "optimization_level",
    ]
    with (RESULTS_DIR / "processor_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_report(instance: dict, penalty: float, classical_optimum: dict, parameters: dict, results: list[dict]) -> None:
    synthetic = instance.get("source_status") != "ORGANIZER_SUPPLIED"
    caution = (
        "**DATA STATUS — PROVISIONAL:** This run uses an explicitly synthetic risk matrix because the uploaded PS PDF does not specify numeric 4×4 entries. These results validate the pipeline only and should not be submitted as official-instance results until the data source is confirmed.\n\n"
        if synthetic else ""
    )
    lines = [
        "# QFF 2026 Phase 1 Report — O2 Constrained Portfolio Optimization",
        "",
        caution,
        "## Problem definition",
        "",
        f"- Assets: {', '.join(instance['assets'])}",
        f"- Expected-return vector: `{instance['expected_returns']}`",
        f"- Risk weight λ: `{instance['risk_weight_lambda']}`",
        f"- Cardinality constraint: select exactly `{instance['selected_assets_k']}` assets",
        f"- Cardinality penalty P: `{penalty:.6g}` (chosen greater than the full span of the unpenalized finite objective)",
        "- Algorithm: p=1 QAOA; exact statevector objective used for classical parameter optimization; shot-based ideal Aer samples used for processor-topology comparisons.",
        "",
        "## Exact classical reference",
        "",
        f"- Optimal portfolio: {', '.join(classical_optimum['selected_assets'])}",
        f"- Optimal bitstring (asset 4 … asset 1 order): `{classical_optimum['bitstring']}`",
        f"- Best feasible return–risk utility: `{classical_optimum['utility']:.8f}`",
        "",
        "## QAOA parameters",
        "",
        f"- γ: `{parameters['gamma']:.8f}`",
        f"- β: `{parameters['beta']:.8f}`",
        f"- Best optimizer restart: `{parameters['best_restart']}`",
        f"- Best expected scaled cost: `{parameters['best_expected_scaled_cost']:.8f}`",
        "",
        "## Processor A/B comparison",
        "",
        "| Metric | Processor A | Processor B |",
        "|---|---:|---:|",
    ]
    a, b = results
    show_fields = [
        ("Physical processor qubits", "processor_qubits", "{}"),
        ("Compiled circuit qubits", "compiled_qubits", "{}"),
        ("Circuit depth", "depth", "{}"),
        ("CX count", "cx_count", "{}"),
        ("SWAP count (BasicSwap diagnostic)", "swap_count_basic_routing", "{}"),
        ("Valid-portfolio probability", "valid_portfolio_probability", "{:.4f}"),
        ("Optimal-portfolio probability", "optimal_portfolio_probability", "{:.4f}"),
        ("Expected raw utility (all outcomes)", "sampled_expected_utility_all_outcomes", "{:.6f}"),
        ("Expected utility (valid outcomes only)", "sampled_expected_utility_given_valid", "{:.6f}"),
        ("Best sampled valid utility", "best_sampled_valid_utility", "{}"),
        ("Optimality gap", "optimality_gap", "{}"),
    ]
    for label, key, fmt in show_fields:
        va, vb = a.get(key), b.get(key)
        fa = "N/A" if va is None else (fmt.format(va) if isinstance(va, (int, float)) else str(va))
        fb = "N/A" if vb is None else (fmt.format(vb) if isinstance(vb, (int, float)) else str(vb))
        lines.append(f"| {label} | {fa} | {fb} |")
    lines += [
        "",
        "## Interpretation and limitations",
        "",
        "- This benchmark uses ideal Aer sampling after topology-constrained transpilation. It does **not** represent hardware noise.",
        "- Processor noise has intentionally not been guessed. Add noisy runs only after the organizer's authoritative noise model is confirmed.",
        "- SWAP count is reported from a separate Qiskit BasicSwap routing diagnostic with a fixed trivial initial layout; the compiled CX count and depth come from the matching fixed-layout/basic-routing circuit transpiled into the configured basis gates.",
        "- Four assets are classically enumerable (16 bitstrings). No quantum advantage is claimed; the experiment studies QAOA quality and architecture/compilation overhead.",
        "- Use figures in `figures/` and raw metrics in `processor_comparison.csv` for the final report.",
        "",
        "## Reproducibility",
        "",
        "Run `python main.py` from the repository root in the environment described by `requirements.txt`.",
        "",
        "## AI assistance disclosure",
        "",
        "Complete this section according to the current policy announced by the QFF 2026 Hackathon & Competitions Cell.",
    ]
    (RESULTS_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    instance = load_instance(DATA_PATH)
    returns = np.asarray(instance["expected_returns"], dtype=float)
    risk = np.asarray(instance["risk_matrix"], dtype=float)
    lam = float(instance["risk_weight_lambda"])
    k = int(instance["selected_assets_k"])
    n = int(instance["n_assets"])

    penalty = instance.get("penalty_weight")
    if penalty is None:
        penalty = choose_penalty_weight(returns, risk, lam, n)
    penalty = float(penalty)
    validate_qubo_conversion(instance, penalty)

    if instance.get("source_status") != "ORGANIZER_SUPPLIED":
        print("WARNING: risk matrix is synthetic development data, not verified organizer data.")
    print("[1/5] Enumerating the exact classical reference ...")
    all_solutions = enumerate_solutions(instance, penalty)
    feasible = [row for row in all_solutions if row["feasible"]]
    if not feasible:
        raise RuntimeError("No feasible portfolios found; check the cardinality constraint.")
    optimum = max(feasible, key=lambda row: row["utility"])

    print("[2/5] Optimizing p=1 QAOA parameters with exact statevector expectations ...")
    parameters = optimize_qaoa(
        instance,
        penalty,
        restarts=int(instance.get("classical_restarts", 6)),
        maxiter=int(instance.get("optimizer_maxiter", 300)),
        seed=int(instance.get("random_seed", 2026)),
    )

    processor_a = read_json(PROCESSOR_DIR / "processor_A.json")
    processor_b = read_json(PROCESSOR_DIR / "processor_B.json")
    print("[3/5] Running topology-constrained ideal Aer comparisons on Processor A and B ...")
    results = []
    for idx, processor in enumerate((processor_a, processor_b)):
        result = sample_processor(
            instance=instance,
            penalty=penalty,
            parameters=parameters,
            processor=processor,
            shots=int(instance.get("shots", 4096)),
            seed=int(instance.get("random_seed", 2026)) + idx,
        )
        # Do not serialize the Qiskit circuit object into result summaries.
        circuit = result.pop("transpiled_circuit")
        circuit_path = RESULTS_DIR / f"compiled_{processor['name'].lower().replace(' ', '_')}.qasm"
        try:
            circuit_path.write_text(circuit.qasm(), encoding="utf-8")
        except Exception:
            # Qiskit 2.x supports OpenQASM 3 export; retain circuit metrics if export API differs.
            try:
                from qiskit import qasm3
                circuit_path = RESULTS_DIR / f"compiled_{processor['name'].lower().replace(' ', '_')}.qasm"
                circuit_path.write_text(qasm3.dumps(circuit), encoding="utf-8")
            except Exception as exc:
                print(f"Note: circuit export skipped for {processor['name']}: {exc}")
        results.append(result)

    print("[4/5] Writing tables, figures, and report ...")
    make_instance_plot(instance, all_solutions)
    make_coupling_plot(processor_a, processor_b)
    for row in results:
        make_distribution_plot(row["sampled_distribution"], row["processor"])
    write_comparison_csv(results)
    write_json(RESULTS_DIR / "classical_solutions.json", {"all_solutions": all_solutions, "exact_optimum": optimum})
    write_json(RESULTS_DIR / "qaoa_parameters.json", {k: v for k, v in parameters.items() if k != "cost_model"})
    write_json(RESULTS_DIR / "run_metadata.json", {
        "problem_code": "O2",
        "source_status": instance.get("source_status"),
        "source_note": instance.get("source_note"),
        "penalty_weight": penalty,
        "risk_matrix_min_eigenvalue": instance.get("risk_matrix_min_eigenvalue"),
        "optimizer": "Nelder-Mead multi-start with exact Statevector expectations",
        "simulation": "ideal Aer shot sampling after topology-constrained transpilation; no noise model configured",
        "reproducibility_seed": int(instance.get("random_seed", 2026)),
    })
    write_report(instance, penalty, optimum, parameters, results)

    print("[5/5] Finished.")
    print(f"Exact optimal portfolio: {', '.join(optimum['selected_assets'])} (utility={optimum['utility']:.6f})")
    print(f"QAOA parameters: gamma={parameters['gamma']:.6f}, beta={parameters['beta']:.6f}")
    for row in results:
        print(
            f"{row['processor']}: CX={row['cx_count']}, depth={row['depth']}, "
            f"SWAP diagnostic={row['swap_count_basic_routing']}, "
            f"valid probability={row['valid_portfolio_probability']:.3f}"
        )
    print(f"Artifacts: {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ImportError as exc:
        print("Missing dependency. Create the documented virtual environment and install requirements.txt.", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        raise
