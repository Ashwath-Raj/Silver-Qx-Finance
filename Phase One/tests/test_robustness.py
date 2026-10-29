import csv
import math
from pathlib import Path

from src.robustness import paired_comparison_rows

ROOT = Path(__file__).resolve().parents[1]


def load_trials():
    with (ROOT / "results/tables/robustness_trials.csv").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_paired_seed_analysis_has_one_reference_contrast_and_three_metrics():
    summaries = paired_comparison_rows(load_trials())
    assert len(summaries) == 3
    assert len({row["comparison"] for row in summaries}) == 1
    assert all(row["n_pairs"] == 10 for row in summaries)
    for row in summaries:
        assert len(row["paired_seeds"].split(",")) == 10
        assert math.isfinite(row["mean_delta_comparison_minus_baseline"])
        assert row["ci95_low_paired_t"] <= row["mean_delta_comparison_minus_baseline"] <= row["ci95_high_paired_t"]


def test_paired_seed_analysis_rejects_missing_seed_pair():
    rows = load_trials()
    filtered = [row for row in rows if not (
        row["processor_family"] == "Processor A"
        and row["topology_label"] == "Master Guide reference"
        and int(row["simulator_seed"]) == 336
    )]
    try:
        paired_comparison_rows(filtered)
    except ValueError as exc:
        assert "seed mismatch" in str(exc)
    else:
        raise AssertionError("The paired analysis accepted mismatched seed sets")
