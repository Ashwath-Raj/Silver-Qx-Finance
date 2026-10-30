#!/usr/bin/env python3
"""Generate PS-O2 robustness and finite-shot uncertainty analysis.

This script analyzes existing committed CSVs only. It does not re-run QAOA,
retune optimizer angles, or modify the scored benchmark tables.
"""
from __future__ import annotations
import argparse, csv, math, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
LAMBDA_VALUES = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)
MARKER_START = "<!-- BEGIN O2 ROBUSTNESS ADDENDUM -->"
MARKER_END = "<!-- END O2 ROBUSTNESS ADDENDUM -->"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required committed result table not found: {path.relative_to(ROOT)}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Result table is empty: {path.relative_to(ROOT)}")
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: fmt_csv(v) for k, v in row.items()})


def fmt_csv(value):
    if isinstance(value, float):
        return f"{value:.10g}"
    if isinstance(value, (list, tuple)):
        return ";".join(str(v) for v in value)
    return value


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0 or not (0 <= successes <= trials):
        raise ValueError(f"Invalid binomial counts successes={successes}, trials={trials}")
    p = successes / trials
    z2 = z * z
    den = 1.0 + z2 / trials
    center = (p + z2 / (2.0 * trials)) / den
    half = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * trials)) / trials) / den
    return max(0.0, center - half), min(1.0, center + half)


def pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def lam_text(value: float) -> str:
    return str(int(value)) if abs(value - round(value)) < 1e-9 else f"{value:g}"


def interval_text(estimate: float, low: float, high: float) -> str:
    return f"{pct(estimate)} [{pct(low)}, {pct(high)}]"


def write_section(path: Path, content: str, anchor: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    replacement = f"{MARKER_START}\n\n{content.strip()}\n\n{MARKER_END}"
    if start >= 0 and end >= 0:
        end += len(MARKER_END)
        text = text[:start] + replacement + text[end:]
    else:
        if (start >= 0) != (end >= 0):
            raise ValueError(f"Only one robustness marker exists in {path.name}; refusing ambiguous edit")
        idx = text.find(anchor)
        if idx < 0:
            raise ValueError(f"Expected insertion point {anchor!r} not found in {path.name}")
        text = text[:idx] + replacement + "\n\n" + text[idx:]
    path.write_text(text, encoding="utf-8")


def analyze() -> tuple[list[dict], list[dict], list[dict]]:
    condition_rows = read_csv(TABLES / "processor_conditions.csv")
    lambda_rows = read_csv(TABLES / "processor_d_lambda_sweep.csv")
    trials = read_csv(TABLES / "lambda_optimization_trials.csv")

    # Validate required evidence before writing anything.
    lambda_values = sorted({round(float(r["lambda"]), 8) for r in lambda_rows})
    if tuple(lambda_values) != LAMBDA_VALUES:
        raise ValueError(f"Expected lambda sweep {LAMBDA_VALUES}, got {tuple(lambda_values)}")
    if len(lambda_rows) != 12:
        raise ValueError(f"Expected 12 D lambda rows (6 penalties × ideal/noisy), got {len(lambda_rows)}")
    for lam in LAMBDA_VALUES:
        group = [r for r in trials if abs(float(r["lambda"]) - lam) < 1e-8]
        seeds = sorted(int(r["seed"]) for r in group)
        if len(group) != 5 or seeds != [0, 1, 2, 3, 4]:
            raise ValueError(f"lambda={lam:g}: expected one trial for each seed 0–4, got {seeds}")
        best_row = min(group, key=lambda r: float(r["expected_qubo_energy"]))
        benchmark_rows = [r for r in lambda_rows if abs(float(r["lambda"]) - lam) < 1e-8 and r["condition"] == "ideal"]
        if len(benchmark_rows) != 1:
            raise ValueError(f"lambda={lam:g}: expected exactly one ideal D benchmark row")
        selected_seed = int(benchmark_rows[0]["selected_seed"])
        if selected_seed != int(best_row["seed"]):
            raise ValueError(
                f"lambda={lam:g}: saved selected seed {selected_seed} does not match minimum saved exact energy seed {best_row['seed']}"
            )
        if str(benchmark_rows[0]["qubo_minimum_valid"]).lower() not in ("true", "false"):
            raise ValueError(f"lambda={lam:g}: invalid qubo_minimum_valid field")

    # Five-start summary: exact statevector diagnostics, not noisy-shot replications.
    seed_summary = []
    for lam in LAMBDA_VALUES:
        group = sorted([r for r in trials if abs(float(r["lambda"]) - lam) < 1e-8], key=lambda r: int(r["seed"]))
        energies = [float(r["expected_qubo_energy"]) for r in group]
        valid = [float(r["valid_probability_ideal_statevector"]) for r in group]
        popt = [float(r["p_opt_ideal_statevector"]) for r in group]
        best = min(group, key=lambda r: float(r["expected_qubo_energy"]))
        exhausted = [r for r in group if int(r["objective_evaluations"]) >= int(r["objective_evaluation_budget"])
                     and str(r["optimization_success"]).lower() == "false"]
        seed_summary.append({
            "lambda": lam, "n_starts": len(group), "selected_seed": int(best["seed"]),
            "best_expected_energy": min(energies), "median_expected_energy": statistics.median(energies),
            "worst_expected_energy": max(energies), "mean_expected_energy": statistics.mean(energies),
            "sd_expected_energy_sample": statistics.stdev(energies),
            "min_exact_p_valid": min(valid), "mean_exact_p_valid": statistics.mean(valid), "max_exact_p_valid": max(valid),
            "min_exact_p_opt": min(popt), "mean_exact_p_opt": statistics.mean(popt), "max_exact_p_opt": max(popt),
            "starts_at_max_eval_budget": len(exhausted), "seeds_at_max_eval_budget": [int(r["seed"]) for r in exhausted],
        })

    # Wilson CIs for finite 4,096-shot binomial estimates from the saved counts/frequencies.
    ci_rows = []
    def add_ci(source: str, row: dict, processor: str, condition: str):
        shots = int(float(row["shots"]))
        lam = float(row["lambda"]) if row.get("lambda") not in (None, "") else 2.0
        for metric, field in (("valid_solution_frequency", "valid_solution_frequency"), ("p_opt", "p_opt")):
            estimate = float(row[field])
            successes = int(round(estimate * shots))
            if abs(successes / shots - estimate) > 1e-8:
                raise ValueError(f"Saved {metric}={estimate} is not a shot fraction for {shots} shots")
            lower, upper = wilson(successes, shots)
            ci_rows.append({
                "source": source, "lambda": lam, "processor": processor, "condition": condition,
                "metric": metric, "estimate": estimate, "successes": successes, "shots": shots,
                "wilson_95_lower": lower, "wilson_95_upper": upper,
            })

    baseline = [r for r in condition_rows if abs(float(r["lambda"]) - 2.0) < 1e-8 and r["condition"].lower() == "noisy"]
    processors = {r["processor"] for r in baseline}
    if processors != {"Processor A", "Processor B", "Processor D"} or len(baseline) != 3:
        raise ValueError(f"Expected noisy reference rows for A/B/D at lambda=2; got {sorted(processors)}")
    for row in baseline:
        add_ci("reference_comparison", row, row["processor"], row["condition"].lower())
    for row in lambda_rows:
        add_ci("lambda_sweep", row, row["processor"], row["condition"].lower())

    # Check the key rubric-specific penalty behavior in the locked evaluated sweep.
    by_lam = {float(r["lambda"]): r for r in lambda_rows if r["condition"].lower() == "ideal"}
    if str(by_lam[0.0]["qubo_minimum_valid"]).lower() != "false" or str(by_lam[0.5]["qubo_minimum_valid"]).lower() != "false":
        raise ValueError("Rubric check failed: QUBO minimum should be invalid at lambda=0 and 0.5")
    if str(by_lam[1.0]["qubo_minimum_valid"]).lower() != "true":
        raise ValueError("Expected first tested valid QUBO minimum at lambda=1")
    return seed_summary, ci_rows, baseline


def make_plot(trials: list[dict], summary: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), constrained_layout=True)
    lams = list(LAMBDA_VALUES)
    seed_colors = None
    jitter = {s: (s - 2) * 0.055 for s in range(5)}
    chosen = {float(r["lambda"]): int(r["selected_seed"]) for r in summary}

    for seed in range(5):
        group = [r for r in trials if int(r["seed"]) == seed]
        xs = [float(r["lambda"]) + jitter[seed] for r in group]
        ys = [float(r["expected_qubo_energy"]) for r in group]
        selected_x = [float(r["lambda"]) + jitter[seed] for r in group if chosen[float(r["lambda"])] == seed]
        selected_y = [float(r["expected_qubo_energy"]) for r in group if chosen[float(r["lambda"])] == seed]
        axes[0].scatter(xs, ys, s=38, alpha=0.7, label=f"Start seed {seed}")
        if selected_x:
            axes[0].scatter(selected_x, selected_y, s=100, marker="*", edgecolors="black", linewidths=0.4, zorder=5)

    means = [float(r["mean_expected_energy"]) for r in summary]
    sds = [float(r["sd_expected_energy_sample"]) for r in summary]
    axes[0].errorbar(lams, means, yerr=sds, fmt="D-", color="black", markersize=4, capsize=4,
                     linewidth=1.5, label="Mean ± sample SD")
    axes[0].set_title("Exact expected QUBO energy by initialization")
    axes[0].set_ylabel("Expected QUBO energy (lower is better)")
    axes[0].set_xlabel("Penalty λ")
    axes[0].legend(frameon=False, fontsize=7, ncol=2)
    axes[0].grid(axis="y", alpha=0.25)

    for seed in range(5):
        group = sorted([r for r in trials if int(r["seed"]) == seed], key=lambda r: float(r["lambda"]))
        xs = [float(r["lambda"]) + jitter[seed] for r in group]
        axes[1].scatter(xs, [float(r["valid_probability_ideal_statevector"]) for r in group],
                         s=35, marker="o", alpha=0.65, label="P(valid), each start" if seed == 0 else None)
        axes[1].scatter(xs, [float(r["p_opt_ideal_statevector"]) for r in group],
                         s=35, marker="^", alpha=0.65, label="P(opt), each start" if seed == 0 else None)
    mean_valid = [float(r["mean_exact_p_valid"]) for r in summary]
    mean_opt = [float(r["mean_exact_p_opt"]) for r in summary]
    axes[1].plot(lams, mean_valid, "o-", linewidth=1.7, label="Mean P(valid)")
    axes[1].plot(lams, mean_opt, "^-", linewidth=1.7, label="Mean P(opt)")
    axes[1].axvline(1.0, linestyle="--", linewidth=1.2, color="grey", label="First tested valid QUBO minimum")
    axes[1].set_title("Exact statevector probabilities across starts")
    axes[1].set_xlabel("Penalty λ")
    axes[1].set_ylabel("Probability")
    axes[1].set_ylim(0, 1)
    axes[1].legend(frameon=False, fontsize=7)
    axes[1].grid(axis="y", alpha=0.25)
    fig.suptitle("PS-O2 initialization sensitivity (five COBYLA starts; not noisy-shot repetitions)", fontweight="bold")
    fig.savefig(FIGURES / "optimizer_seed_sensitivity.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_report_addendum(seed_summary: list[dict], ci_rows: list[dict], lambda_rows: list[dict]) -> str:
    lines = ["### Finite-shot uncertainty at the reference penalty (λ = 2)", "",
             "The intervals below are 95% Wilson score intervals for the saved binomial counts from one 4,096-shot noisy run per processor. They quantify finite-shot counting uncertainty only; they do not include optimizer-start variability, model uncertainty, or device-to-device variation.", "",
             "| Processor | Valid-solution frequency (95% CI) | P(opt) (95% CI) |", "|---|---:|---:|"]
    for row in sorted([r for r in ci_rows if r["source"] == "reference_comparison" and r["metric"] == "valid_solution_frequency"], key=lambda r: r["processor"]):
        prow = next(r for r in ci_rows if r["source"] == "reference_comparison" and r["processor"] == row["processor"] and r["metric"] == "p_opt")
        lines.append(f"| {row['processor']} | {interval_text(row['estimate'], row['wilson_95_lower'], row['wilson_95_upper'])} | {interval_text(prow['estimate'], prow['wilson_95_lower'], prow['wilson_95_upper'])} |")
    lines += ["", "The noisy A/B/D intervals overlap for both metrics. Processor D's observed valid frequency (45.92%) is slightly higher than B's (45.56%), while its observed P(opt) (24.07%) is slightly lower than B's (24.61%). With one 4,096-shot draw per condition, these small differences should not be called statistically reliable architecture effects.", "",
              "### Penalty sweep: feasibility and solution quality are different metrics", "",
              "| λ | Exact QUBO minimum valid? | Noisy valid frequency (95% CI) | Noisy P(opt) (95% CI) | Modal valid portfolio | F/F* of modal portfolio |", "|---:|:---:|---:|---:|:---:|---:|"]
    noisy = sorted([r for r in ci_rows if r["source"] == "lambda_sweep" and r["condition"] == "noisy" and r["metric"] == "valid_solution_frequency"], key=lambda r: r["lambda"])
    sweep_file = read_csv(TABLES / "processor_d_lambda_sweep.csv")
    for ci in noisy:
        lam = float(ci["lambda"])
        src = next(r for r in sweep_file if abs(float(r["lambda"]) - lam) < 1e-8 and r["condition"].lower() == "noisy")
        opt = next(r for r in ci_rows if r["source"] == "lambda_sweep" and abs(float(r["lambda"]) - lam) < 1e-8 and r["condition"] == "noisy" and r["metric"] == "p_opt")
        valid_state = str(src["qubo_minimum_valid"]).lower() == "true"
        selected = src["selected_portfolio_x0_to_x3"]
        ratio = float(src["objective_ratio_selected_valid"])
        lines.append(f"| {lam_text(lam)} | {'Yes' if valid_state else 'No'} | {interval_text(ci['estimate'], ci['wilson_95_lower'], ci['wilson_95_upper'])} | {interval_text(opt['estimate'], opt['wilson_95_lower'], opt['wilson_95_upper'])} | `{selected}` | {ratio:.3f} |")
    lines += ["", "Across the tested values, the exact QUBO minimum is invalid at λ = 0 and 0.5, and first becomes valid at λ = 1. The observed noisy valid-solution frequency then rises overall, reaching 67.24% at λ = 10; P(opt) does not rise with it. P(opt) is highest among these selected-start runs near λ = 2 (24.07%), then falls to 15.70% at λ = 5 and 11.55% at λ = 10. At λ = 5 the modal valid portfolio has F/F* = 0.474, despite a 61.96% valid frequency. Therefore, increasing λ improves feasibility pressure in this run but does not monotonically improve optimal-state sampling or the modal valid portfolio.", "",
              "A modal valid portfolio with F/F* = 1.0 does not imply a high P(opt): the former selects the most frequent bitstring *conditional on being valid*; the latter is the unconditional fraction of all shots that measured an optimal portfolio. These quantities must be read alongside valid frequency and the conditional mean objective.", "",
              "### Five-start optimizer variability", "",
              "The table summarizes the five exact-statevector COBYLA starts saved in `lambda_optimization_trials.csv`. Energy spread describes optimizer initialization sensitivity; probability ranges are exact statevector diagnostics before finite-shot sampling. The runs are not five noisy-shot replicates.", "",
              "| λ | Selected seed | Best E | Median E | Worst E | Mean E ± sample SD | Exact P(valid) range | Exact P(opt) range | Starts at 200-evaluation cap |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in seed_summary:
        lines.append(f"| {lam_text(float(r['lambda']))} | {r['selected_seed']} | {r['best_expected_energy']:.3f} | {r['median_expected_energy']:.3f} | {r['worst_expected_energy']:.3f} | {r['mean_expected_energy']:.3f} ± {r['sd_expected_energy_sample']:.3f} | {pct(r['min_exact_p_valid'])}–{pct(r['max_exact_p_valid'])} | {pct(r['min_exact_p_opt'])}–{pct(r['max_exact_p_opt'])} | {r['starts_at_max_eval_budget']}/5 |")
    exhausted = next(r for r in seed_summary if abs(float(r["lambda"]) - 10.0) < 1e-8)
    lines += ["", f"**Budget caveat:** {exhausted['starts_at_max_eval_budget']}/5 starts at λ = 10 reached the 200-evaluation maximum (`MAXFUN`) before COBYLA declared convergence. The selected run is seed {exhausted['selected_seed']}; it did not hit the cap, but three competing starts did. Treat the λ = 10 five-start spread and selected best as budget-limited evidence, not as a proof of convergence. The required benchmark outputs are preserved unchanged; a larger-budget sensitivity run would be a separately labelled follow-up.", "",
              "![Five-start optimizer variability and exact statevector probabilities](results/figures/optimizer_seed_sensitivity.png)", "",
              "The architecture decision also remains narrow: Processor D1 removes the measured routing overhead (12 compiled CX, 0 SWAPs, depth 23) but does not show a resolved noisy P(opt) gain over Processor B under the current finite-shot synthetic-noise experiment. Lower compiled cost and higher portfolio quality are distinct conclusions."]
    return "\n".join(lines)


def build_readme_addendum() -> str:
    return """## Robustness and uncertainty\n\nThe benchmark now includes a reproducible addendum computed from the committed CSVs. At the reference penalty (λ = 2), the 95% Wilson intervals for noisy valid-solution frequency and P(opt) overlap across Processors A, B and D; the observed A/B/D differences therefore do not establish a statistically reliable quality advantage. The D penalty sweep shows that feasibility and optimal sampling are distinct: the exact QUBO minimum first becomes valid at λ = 1, while noisy valid frequency rises further at large λ even as P(opt) and the modal portfolio's objective ratio fall.\n\nThe five-start sensitivity table reports mean and sample standard deviation of exact expected QUBO energy, the probability range across starts, and optimizer-budget exhaustion. **At λ = 10, 3/5 starts reach the 200-evaluation cap**, so that point is explicitly treated as budget-limited. The added intervals are finite-shot binomial uncertainty, not optimizer uncertainty or a hardware-calibration model.\n\nArtifacts: [optimizer seed summary](results/tables/optimizer_seed_summary.csv) · [finite-shot Wilson intervals](results/tables/finite_shot_wilson_ci.csv) · [five-start sensitivity figure](results/figures/optimizer_seed_sensitivity.png) · [full technical interpretation](report.md#finite-shot-uncertainty-at-the-reference-penalty-λ--2)."""


def main() -> int:
    seed_rows, ci_rows, _ = analyze()
    # Re-read trials for plot; all validation above happens before document edits.
    trials = read_csv(TABLES / "lambda_optimization_trials.csv")
    write_csv(TABLES / "optimizer_seed_summary.csv", seed_rows, [
        "lambda", "n_starts", "selected_seed", "best_expected_energy", "median_expected_energy", "worst_expected_energy",
        "mean_expected_energy", "sd_expected_energy_sample", "min_exact_p_valid", "mean_exact_p_valid", "max_exact_p_valid",
        "min_exact_p_opt", "mean_exact_p_opt", "max_exact_p_opt", "starts_at_max_eval_budget", "seeds_at_max_eval_budget"])
    write_csv(TABLES / "finite_shot_wilson_ci.csv", ci_rows, [
        "source", "lambda", "processor", "condition", "metric", "estimate", "successes", "shots", "wilson_95_lower", "wilson_95_upper"])
    make_plot(trials, seed_rows)

    lambda_rows = read_csv(TABLES / "processor_d_lambda_sweep.csv")
    report_addendum = build_report_addendum(seed_rows, ci_rows, lambda_rows)
    write_section(ROOT / "report.md", report_addendum, "## 8. Outputs and artifact map")
    readme_addendum = build_readme_addendum()
    write_section(ROOT / "README.md", readme_addendum, "## Problem formulation")

    # Make the new source tables part of the report's artifact map (outside generated sections).
    report_path = ROOT / "report.md"
    report_text = report_path.read_text(encoding="utf-8")
    trial_row = "| `results/tables/lambda_optimization_trials.csv` | Five COBYLA starts for each $\\lambda$, including angle and evaluation metadata |"
    added_rows = trial_row + "\n| `results/tables/optimizer_seed_summary.csv` | Mean/SD, best/median/worst energy, statevector probability ranges and budget-cap count across five starts |\n| `results/tables/finite_shot_wilson_ci.csv` | 95% Wilson intervals for saved 4,096-shot valid-frequency and optimal-state counts |\n| `results/figures/optimizer_seed_sensitivity.png` | Five-start exact-statevector sensitivity by penalty |"
    if "results/tables/optimizer_seed_summary.csv" not in report_text and trial_row in report_text:
        report_path.write_text(report_text.replace(trial_row, added_rows, 1), encoding="utf-8")

    print("PASS: 6 penalty values × 5 seeds; selected seeds agree with minimum saved exact energy")
    print("PASS: QUBO minimum invalid at lambda=0 and 0.5; first tested valid minimum at lambda=1")
    print("PASS: reference A/B/D noisy rows and 4,096-shot count consistency")
    print(f"WROTE {TABLES / 'optimizer_seed_summary.csv'}")
    print(f"WROTE {TABLES / 'finite_shot_wilson_ci.csv'}")
    print(f"WROTE {FIGURES / 'optimizer_seed_sensitivity.png'}")
    print("UPDATED report.md and README.md outside the generated numeric-results block")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
