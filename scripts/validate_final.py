#!/usr/bin/env python3
"""Read-only final PS-O2 preflight for selected Processor D1."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "qff_phase2.py": "04be4fa610ba60854a2b3b9237891df7e8ade62e2fcd9659076e36e794f077ab",
    "data/instances.json": "9b5738e6c6c13208599c63aae97ec0549bf993c810bcda278ff8795a684ad09d",
}
D1_EDGES = {(0,1),(0,2),(0,3),(0,4),(1,2),(1,3),(2,3),(4,5)}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""):
            h.update(b)
    return h.hexdigest()

def main() -> int:
    sys.dont_write_bytecode = True
    for rel, expected in EXPECTED.items():
        actual = sha(ROOT/rel)
        if actual != expected:
            raise SystemExit(f"FAIL: locked hash mismatch for {rel}: {actual}")
        print(f"PASS locked SHA-256: {rel}")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import qff_phase2 as qff
    locked = json.loads((ROOT/"data/instances.json").read_text())["PS-O2"]
    derived = json.loads((ROOT/"data/instance.json").read_text())
    for key in ("expected_returns","risk_matrix","risk_aversion_q","k","required_lambda_sweep"):
        if derived.get(key) != locked.get(key):
            raise SystemExit(f"FAIL: data/instance.json mismatch for {key}")
    print("PASS derived PS-O2 instance matches locked organizer data")
    ddoc = json.loads((ROOT/"processors/processor_D.json").read_text())
    d = qff.load_processor(str(ROOT/"processors/processor_D.json"))
    violations = qff.validate_processor_d(d, required_qubits=4)
    if violations:
        raise SystemExit("FAIL Processor D validation: " + "; ".join(violations))
    edges = {tuple(sorted(map(int,e))) for e in ddoc["edges"]}
    if ddoc.get("selection_status") != "selected" or ddoc.get("selection_id") != "D1_K4_TAIL_6Q":
        raise SystemExit("FAIL Processor D is not marked as selected D1")
    if ddoc.get("num_qubits") != 6 or edges != D1_EDGES:
        raise SystemExit("FAIL Processor D does not match the selected six-qubit D1 topology")
    if ddoc.get("basis_gates") != ["rz","sx","x","cx"]:
        raise SystemExit("FAIL Processor D basis gate list differs from official requirement")
    if ddoc.get("noise") != {"model":"official","p1":0.001,"p2":0.005,"p_readout":0.01}:
        raise SystemExit("FAIL Processor D noise rates differ from official model")
    print("PASS official validate_processor_d: D1 K4-tail is valid for PS-O2")
    print("PASS D1 topology, gate set, noise floor, and selection marker")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
