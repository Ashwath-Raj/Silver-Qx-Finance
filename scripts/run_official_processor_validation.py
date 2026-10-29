#!/usr/bin/env python3
"""Run the organizer's official Processor D validation when Qiskit is installed."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
try:
    from qff_phase2 import load_processor, validate_processor_d
except ImportError as exc:
    raise SystemExit(f"Qiskit/Aer dependency unavailable: {exc}. Install requirements.txt first.")
D=load_processor(ROOT/'processors/processor_D.json')
errors=validate_processor_d(D,required_qubits=4)
if errors:
    print('FAIL')
    print('\n'.join(errors))
    raise SystemExit(1)
print('Official Processor D validation: PASS')
print('Qubits:',D['num_qubits'],'edges:',len(D['edges']))
