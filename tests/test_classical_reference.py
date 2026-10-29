from pathlib import Path
import numpy as np
from src.classical_reference import load_instance, enumerate_reference, objective, qubo_energy, qubo_matrix

ROOT=Path(__file__).resolve().parents[1]

def test_locked_phase2_ps_o2_parameters():
    instance=load_instance(ROOT/'data/instance.json')
    assert instance['expected_returns']==[5,3,4,2]
    assert instance['risk_aversion_q']==0.5
    assert instance['k']==2
    assert instance['required_lambda_sweep']==[0,0.5,1,2,5,10]

def test_exact_enumeration_and_constraint_count():
    result=enumerate_reference(load_instance(ROOT/'data/instance.json'))
    assert result['state_count']==16
    assert result['valid_portfolio_count']==6
    assert len(result['optimal_portfolios'])>=1
    assert all(r['valid'] and r['selected_count']==2 for r in result['optimal_portfolios'])

def test_qubo_matrix_matches_direct_energy_for_all_states():
    inst=load_instance(ROOT/'data/instance.json')
    mu=np.asarray(inst['expected_returns'],dtype=float); sigma=np.asarray(inst['risk_matrix'],dtype=float)
    q=float(inst['risk_aversion_q']); k=int(inst['k']); lam=2.0
    Q,c=qubo_matrix(mu,sigma,q,k,lam)
    from src.classical_reference import all_bitstrings
    for x in all_bitstrings(4):
        xv=np.asarray(x,dtype=float)
        direct=qubo_energy(x,mu,sigma,q,k,lam)
        assert np.isclose(xv@Q@xv+c,direct,atol=1e-9)

def test_required_penalty_sweep_has_six_values():
    result=enumerate_reference(load_instance(ROOT/'data/instance.json'))
    assert [r['lambda'] for r in result['exact_penalty_sweep']]==[0,0.5,1,2,5,10]

def test_qaoa_statevector_is_normalized_and_seeded_runs_are_reproducible():
    from src.qaoa_statevector import build_costs, qaoa_state, optimize_restarts
    inst=load_instance(ROOT/'data/instance.json')
    states,costs,_=build_costs(inst,2.0)
    psi=qaoa_state(0.43,1.17,costs,4)
    assert np.isclose(np.vdot(psi,psi).real,1.0,atol=1e-10)
    a=optimize_restarts(inst,penalty=2.0,seeds=(2,),maxiter=80)[0]
    b=optimize_restarts(inst,penalty=2.0,seeds=(2,),maxiter=80)[0]
    assert np.isclose(a['gamma'],b['gamma'])
    assert np.isclose(a['beta'],b['beta'])
    assert 0.0 <= a['valid_probability_ideal_statevector'] <= 1.0


def test_phase2_exact_optimum_value_and_assets():
    result=enumerate_reference(load_instance(ROOT/'data/instance.json'))
    assert np.isclose(result['classical_optimum_F_star'],4.75)
    assert [r['bitstring_x0_to_xn'] for r in result['optimal_portfolios']]==['1100']
    assert result['optimal_portfolios'][0]['selected_indices']==[0,1]
