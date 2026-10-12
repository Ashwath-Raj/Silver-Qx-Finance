"""Tests for Master Guide PS-O2 QUBO/Ising arithmetic."""
import unittest
from pathlib import Path
import numpy as np
from src.portfolio_model import load_instance, validate_qubo_conversion, enumerate_solutions, qubo_matrix
ROOT=Path(__file__).resolve().parents[1]
class PortfolioModelTests(unittest.TestCase):
    def setUp(self):
        self.data=load_instance(ROOT/"data/portfolio_instance.json")
        if self.data.get("q") is None: self.data["q"]=1.0
    def test_master_guide_inputs(self):
        self.assertEqual(self.data["expected_returns"],[0.12,0.18,0.10,0.22])
        self.assertEqual(self.data["selected_assets_k"],2)
        self.assertTrue(np.allclose(self.data["risk_matrix"],np.array([[.04,.01,.02,.01],[.01,.09,.01,.03],[.02,.01,.05,.02],[.01,.03,.02,.08]])))
    def test_risk_matrix_symmetric_psd(self):
        s=np.asarray(self.data["risk_matrix"]); self.assertTrue(np.allclose(s,s.T)); self.assertGreaterEqual(np.linalg.eigvalsh(s).min(),-1e-8)
    def test_qubo_matrix_and_ising_all_16_states(self):
        validate_qubo_conversion(self.data)
    def test_six_feasible_portfolios(self):
        rows=enumerate_solutions(self.data); self.assertEqual(sum(r["feasible"] for r in rows),6)
    def test_qubo_matrix_shape_and_constant(self):
        Q,c=qubo_matrix(self.data); self.assertEqual(Q.shape,(4,4)); self.assertAlmostEqual(c,self.data["cardinality_penalty_A"]*4)
if __name__=="__main__": unittest.main()
