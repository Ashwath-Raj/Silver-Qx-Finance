"""Paired-seed summaries for the QFF synthetic-noise robustness experiment.

Differences are computed within the same simulator seed. Confidence intervals are
exploratory paired t intervals over the selected seeds, not hardware uncertainty.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

import numpy as np
from scipy.stats import t as student_t

METRICS = (
    "valid_portfolio_probability",
    "optimal_portfolio_probability",
    "sampled_expected_utility_given_valid",
)

COMPARISONS = (
    {
        "label": "Processor B reference minus Processor A reference",
        "baseline": ("Processor A", "Master Guide reference"),
        "comparison": ("Processor B", "Master Guide reference"),
    },
)

def paired_comparison_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize the predeclared reference-processor contrast for each robustness metric.

    The delta convention is comparison minus baseline. All compared groups must
    have exactly the same unique seed set; silently unpaired comparisons are rejected.
    """
    grouped: dict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
    for raw in rows:
        family = str(raw["processor_family"])
        topology = str(raw["topology_label"])
        seed = int(raw["simulator_seed"])
        bucket = grouped[(family, topology)]
        if seed in bucket:
            raise ValueError(f"Duplicate robustness row for {(family, topology, seed)}")
        bucket[seed] = raw

    summaries: list[dict[str, Any]] = []
    for comparison in COMPARISONS:
        base_key = comparison["baseline"]
        comp_key = comparison["comparison"]
        if base_key not in grouped or comp_key not in grouped:
            raise ValueError(f"Missing robustness group for comparison: {comparison['label']}")
        base_group = grouped[base_key]
        comp_group = grouped[comp_key]
        base_seeds = set(base_group)
        comp_seeds = set(comp_group)
        if len(base_seeds) < 2 or base_seeds != comp_seeds:
            raise ValueError(
                f"Paired seed mismatch for {comparison['label']}: "
                f"baseline={sorted(base_seeds)}, comparison={sorted(comp_seeds)}"
            )
        seeds = sorted(base_seeds)
        n = len(seeds)
        critical = float(student_t.ppf(0.975, df=n - 1))
        for metric in METRICS:
            baseline_values = [float(base_group[seed][metric]) for seed in seeds]
            comparison_values = [float(comp_group[seed][metric]) for seed in seeds]
            if not np.all(np.isfinite(baseline_values + comparison_values)):
                raise ValueError(f"Non-finite values for {comparison['label']} / {metric}")
            deltas = [right - left for left, right in zip(baseline_values, comparison_values)]
            delta_mean = mean(deltas)
            delta_sd = stdev(deltas)
            half_width = critical * delta_sd / np.sqrt(n)
            summaries.append({
                "comparison": comparison["label"],
                "metric": metric,
                "n_pairs": n,
                "paired_seeds": ",".join(str(seed) for seed in seeds),
                "baseline_mean": mean(baseline_values),
                "comparison_mean": mean(comparison_values),
                "mean_delta_comparison_minus_baseline": delta_mean,
                "sample_sd_of_paired_delta": delta_sd,
                "ci95_low_paired_t": delta_mean - half_width,
                "ci95_high_paired_t": delta_mean + half_width,
            })
    return summaries


def plot_paired_differences(rows: list[dict[str, Any]], output: str | Path) -> None:
    """Plot paired differences and 95% t intervals for the two probability metrics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    comparison_keys = ["Processor B reference minus Processor A reference"]
    display_labels = ["B reference − A reference"]
    metric_info = (
        ("valid_portfolio_probability", "Valid-portfolio probability difference (pp)"),
        ("optimal_portfolio_probability", "Optimal-portfolio probability difference (pp)"),
    )
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
    try:
        for ax, (metric, title) in zip(axes, metric_info):
            metric_rows = [row for row in rows if row["metric"] == metric]
            by_label = {row["comparison"]: row for row in metric_rows}
            x, low_err, high_err = [], [], []
            for label in comparison_keys:
                row = by_label[label]
                scale = 100.0
                centre = float(row["mean_delta_comparison_minus_baseline"]) * scale
                lo = float(row["ci95_low_paired_t"]) * scale
                hi = float(row["ci95_high_paired_t"]) * scale
                x.append(centre)
                low_err.append(max(0.0, centre - lo))
                high_err.append(max(0.0, hi - centre))
            y = np.arange(len(display_labels))
            ax.errorbar(x, y, xerr=[low_err, high_err], fmt="o", capsize=4)
            ax.axvline(0.0, linestyle="--", linewidth=1.2, color="black", alpha=0.65)
            ax.set_yticks(y, display_labels)
            ax.invert_yaxis()
            ax.set_title(title)
            ax.set_xlabel("Paired mean difference; positive favours the comparison run")
            ax.grid(axis="x", alpha=0.25)
        fig.suptitle("Paired robustness differences across common simulator seeds")
        fig.tight_layout()
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=180, bbox_inches="tight")
    finally:
        plt.close(fig)
