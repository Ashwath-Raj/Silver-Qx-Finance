"""Offline unit tests for model/QUBO arithmetic (no Qiskit required)."""
import unittest
from pathlib import Path

import numpy as np

from src.portfolio_model import (
    bitvector_from_int,
    choose_penalty_weight,
    enumerate_solutions,
    load_instance,
    qubo_coefficients,
    full_cost,
    validate_qubo_conversion,
)

ROOT = Path(__file__).resolve().parents[1]


class PortfolioModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = load_instance(ROOT / "data" / "portfolio_instance.json")
        cls.returns = np.asarray(cls.instance["expected_returns"], dtype=float)
        cls.risk = np.asarray(cls.instance["risk_matrix"], dtype=float)
        cls.lam = float(cls.instance["risk_weight_lambda"])
        cls.k = int(cls.instance["selected_assets_k"])
        cls.n = int(cls.instance["n_assets"])
        cls.penalty = choose_penalty_weight(cls.returns, cls.risk, cls.lam, cls.n)

    def test_risk_matrix_is_symmetric_psd(self):
        self.assertTrue(np.allclose(self.risk, self.risk.T))
        self.assertGreaterEqual(np.linalg.eigvalsh(self.risk).min(), -1e-8)

    def test_bitvector_little_endian(self):
        self.assertEqual(bitvector_from_int(5, 4).tolist(), [1, 0, 1, 0])

    def test_qubo_and_ising_conversions(self):
        validate_qubo_conversion(self.instance, self.penalty)

    def test_cardinality_optimum_is_feasible(self):
        rows = enumerate_solutions(self.instance, self.penalty)
        feasible = [row for row in rows if row["feasible"]]
        self.assertEqual(len(feasible), 6)  # choose(4, 2)
        optimum = max(feasible, key=lambda row: row["utility"])
        self.assertEqual(optimum["selected_count"], 2)

    def test_penalty_dominates_unpenalized_objective_span(self):
        validate_qubo_conversion(self.instance, self.penalty)
        # Every invalid bitstring has cost strictly above every feasible best
        # candidate, because P exceeds the full unpenalized cost span.
        all_rows = enumerate_solutions(self.instance, self.penalty)
        feasible_costs = [row["cost"] for row in all_rows if row["feasible"]]
        invalid_costs = [row["cost"] for row in all_rows if not row["feasible"]]
        self.assertGreater(min(invalid_costs), max(feasible_costs))


if __name__ == "__main__":
    unittest.main()
