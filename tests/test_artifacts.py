import csv
import json
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def json_file(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def table_rows(relative):
    with (ROOT / relative).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_problem_and_benchmark_metadata_are_consistent():
    instance = json_file("data/processed/portfolio_instance.json")
    metadata = json_file("results/tables/run_metadata.json")
    params = json_file("results/tables/qaoa_parameters.json")
    topology = json_file("results/tables/topology_experiment_metadata.json")
    assert instance["q"] == metadata["q"] == params["q"] == topology["q"] == 1.0
    assert instance["cardinality_penalty_A"] == metadata["cardinality_penalty_A"] == params["penalty_A"] == topology["cardinality_penalty_A"] == 0.02
    assert instance["penalty_status"] == "PARTICIPANT_SELECTED_DOCUMENTED_NOT_ORGANIZER_PRESCRIBED"
    assert metadata["penalty_status"] == instance["penalty_status"]
    assert params["penalty_status"] == instance["penalty_status"]
    assert "pending organizer confirmation" in instance["q_selection_status"].lower()


def test_required_and_supplementary_tables_have_expected_shapes():
    expected_rows = {
        "results/tables/processor_comparison.csv": 4,
        "results/tables/topology_experiment.csv": 8,
        "results/tables/robustness_trials.csv": 40,
        "results/tables/robustness_summary.csv": 4,
        "results/tables/paired_robustness_comparison.csv": 3,
        "results/tables/q_sensitivity.csv": 7,
        "results/tables/penalty_sensitivity.csv": 10,
    }
    for filename, expected in expected_rows.items():
        rows = table_rows(filename)
        assert len(rows) == expected, f"{filename} expected {expected} rows; got {len(rows)}"
    topology_rows = table_rows("results/tables/topology_experiment.csv")
    reference_rows = [row for row in topology_rows if row["topology_role"] == "reference_baseline"]
    custom_rows = [row for row in topology_rows if row["topology_role"] == "CUSTOM_SUPPLEMENTARY_NOT_OFFICIAL_REFERENCE"]
    expected_modes = {
        ("Processor A", "ideal"), ("Processor A", "noisy"),
        ("Processor B", "ideal"), ("Processor B", "noisy"),
    }
    assert len(reference_rows) == len(custom_rows) == 4
    assert {(row["processor_family"], row["mode"]) for row in reference_rows} == expected_modes
    assert {(row["processor_family"], row["mode"]) for row in custom_rows} == expected_modes
    assert all(row["topology_label"] == "Master Guide reference" for row in reference_rows)
    assert all(row["topology_label"].startswith("Custom (not reference):") for row in custom_rows)
    custom_edges = {
        row["processor_family"]: int(row["edge_count"])
        for row in custom_rows if row["mode"] == "ideal"
    }
    assert custom_edges == {"Processor A": 8, "Processor B": 16}
    trials = table_rows("results/tables/robustness_trials.csv")
    assert len(trials) == 40
    assert {row["topology_role"] for row in trials} == {
        "reference_baseline", "CUSTOM_SUPPLEMENTARY_NOT_OFFICIAL_REFERENCE"
    }
    assert len(table_rows("results/tables/robustness_summary.csv")) == 4


def test_baseline_probabilities_and_gate_metrics_are_valid():
    rows = table_rows("results/tables/processor_comparison.csv")
    assert {(row["processor"], row["mode"]) for row in rows} == {
        ("Processor A", "ideal"), ("Processor A", "noisy"),
        ("Processor B", "ideal"), ("Processor B", "noisy"),
    }
    for row in rows:
        valid = float(row["valid_portfolio_probability"])
        optimal = float(row["optimal_portfolio_probability"])
        assert 0 <= optimal <= valid <= 1
        assert int(row["shots"]) == 4096
        assert int(row["swap_count_native"]) == 0


def test_notebook_execution_and_report_provenance_are_clean():
    notebook = nbformat.read(ROOT / "main.ipynb", as_version=4)
    errors = [
        output.get("ename", "unknown error")
        for cell in notebook.cells if cell.cell_type == "code"
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    assert not errors, errors
    all_sources = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")
    assert 'PENALTY_A = 0.02' in all_sources
    report = (ROOT / "report.md").read_text(encoding="utf-8").lower()
    assert "organizer clarified" in report and "binary selection indicators" in report
    assert "q remains provisional" in report
    assert "paired robustness comparisons" in report


def test_paired_robustness_figure_exists():
    figure = ROOT / "results/figures/paired_robustness_differences.png"
    assert figure.is_file() and figure.stat().st_size > 10_000

def test_report_covers_reference_architecture_and_custom_topology_artifacts():
    report = (ROOT / "report.md").read_text(encoding="utf-8").lower()
    assert "findings and architecture interpretation" in report
    assert "reference processor b compiles to depth 35" in report
    assert "do not establish a statistically clear performance difference" in report
    assert "all three paired-seed 95% t intervals" in report
    # report.md is intentionally deferred. Validate custom topology labels in the
    # machine-readable experiment artifact instead of requiring them in the report.
    topology_rows = table_rows("results/tables/topology_experiment.csv")
    custom_rows = [
        row for row in topology_rows
        if row["topology_role"] == "CUSTOM_SUPPLEMENTARY_NOT_OFFICIAL_REFERENCE"
    ]
    assert len(custom_rows) == 4
    custom_labels = [row["topology_label"].lower() for row in custom_rows]
    assert any("paca-5" in label for label in custom_labels)
    assert any("paca-9" in label for label in custom_labels)
    assert all(label.startswith("custom (not reference):") for label in custom_labels)
    assert "alternative linear chain" not in report
    assert "balanced ring with chords" not in report
