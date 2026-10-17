#!/usr/bin/env python3
"""Finalize and package QFF 2026 Phase 1."""

import argparse
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

AI_DISCLOSURE = """## AI-assistance disclosure

AI-based tools were used as support during development for interpreting
requirements, reviewing and drafting code, troubleshooting, and improving
technical documentation. The team remains responsible for the submitted
implementation, experimental design, results, and conclusions. The team should
review and validate the code and reported outputs against the Master Guide.
AI assistance does not replace the classical reference, simulator measurements,
or the limitations stated in this report.

"""

PROCESSOR_D = """## Proposed Processor D — design concept only

**Status:** conceptual proposal only. Processor D was not implemented, executed,
or evaluated in Phase 1. The measured results remain the reference Processor A/B
runs and the separately labelled supplementary topology experiments.

A candidate starting point for a future custom Processor D is a fully connected
four-qubit core (the six pairwise edges of a K4 graph). This can directly represent
all pairwise asset interactions for the four-asset PS-O2 problem when the physical
coupling map and qubit placement support the embedding. Additional qubits should
have a documented purpose, such as providing alternative routing paths. More qubits
or edges alone do not demonstrate improved performance.

Before implementation, document the target backend or synthetic coupling map,
qubit roles, mapping, and noise assumptions. Compare against A/B using matched
QUBO parameters, shot counts, transpilation settings, noise assumptions, and seeds.
Measure feasible-portfolio probability, optimal-portfolio probability, compiled
depth, two-qubit-gate count, routing overhead, and multi-seed uncertainty.

This is a design proposal, not an implemented or tested processor. Processor D
is outside the Phase 1 execution scope.

"""

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".ipynb_checkpoints",
    "node_modules", "site-packages",
}
SKIP_NAMES = {
    ".env", "credentials.json", "service-account.json",
    "id_rsa", "id_ed25519", ".DS_Store", "Thumbs.db",
}
SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib",
    ".pem", ".key", ".p12", ".pfx", ".zip", ".7z", ".rar",
}


def find_root():
    here = Path.cwd().resolve()
    markers = ("README.md", "report.md", "requirements-dev.txt", "src/problem.py")
    for p in (here, *here.parents):
        if all((p / m).is_file() for m in markers):
            return p
    raise RuntimeError(
        "Run from the project root containing README.md, report.md, "
        "requirements-dev.txt, and src/problem.py."
    )


def add_section(path, heading, section, anchor):
    content = path.read_text(encoding="utf-8")
    if heading in content:
        print(f"[OK] {path.name}: section already exists")
        return
    if anchor in content:
        content = content.replace(anchor, section + anchor, 1)
    else:
        content = content.rstrip() + "\n\n" + section
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[UPDATED] {path.name}: added {heading}")


def patch_project(root):
    add_section(
        root / "README.md",
        "## AI-assistance disclosure",
        AI_DISCLOSURE,
        "## Decision-variable interpretation",
    )
    add_section(
        root / "report.md",
        "## Proposed Processor D — design concept only",
        PROCESSOR_D,
        "## Reproducibility and artifacts",
    )

    requirements = root / "requirements-dev.txt"
    lines = [
        line for line in requirements.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("nbconvert>=")
    ]
    if "nbconvert==7.17.2" not in lines:
        lines.append("nbconvert==7.17.2")
    requirements.write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n"
    )
    print("[UPDATED] requirements-dev.txt: aligned nbconvert version")

    script_copy = root / "scripts" / "phase1_finalize.py"
    script_copy.parent.mkdir(parents=True, exist_ok=True)
    this_script = Path(__file__).resolve()
    if this_script != script_copy.resolve():
        shutil.copy2(this_script, script_copy)
        script_copy.chmod(0o755)
    print("[OK] finalizer included under scripts/")


def package(root, output):
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    count = 0
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue

            relative = path.relative_to(root)
            if path.resolve() == output:
                continue
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.name in SKIP_NAMES:
                continue
            if path.name.startswith(".env.") and path.name not in {
                ".env.example", ".env.template"
            }:
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if path.stat().st_size > 200 * 1024 * 1024:
                print(f"[SKIP] large file: {relative}")
                continue

            archive.write(path, relative.as_posix())
            count += 1

    with zipfile.ZipFile(output) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP integrity check failed: {bad_member}")
        names = set(archive.namelist())

    required = {
        "README.md", "report.md", "main.ipynb",
        "processors/processor_A.json", "processors/processor_B.json",
        "requirements.txt", "requirements-dev.txt",
        "PHASE1_PACKAGE_AUDIT.md",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError("Missing required archive files: " + ", ".join(missing))

    print(f"\n[CREATED] {output}")
    print(f"[VERIFIED] ZIP integrity OK; {count} files included")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(Path.home() / "Downloads/QFF_Phase1_Submission.zip"),
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest; the package will not be test-validated.",
    )
    args = parser.parse_args()

    root = find_root()
    print(f"Project root: {root}")

    patch_project(root)

    audit = root / "PHASE1_PACKAGE_AUDIT.md"
    audit.write_text(
        "# Phase 1 package audit\n\n"
        "Cleaned source package for QFF 2026 Phase 1, PS-O2.\n\n"
        "Git metadata, Python environments, caches, credentials, compiled Python "
        "files, nested ZIPs, and files over 200 MB are excluded from the archive. "
        "Source results and parameters are otherwise retained. Processor D is a "
        "proposal only and was not implemented or benchmarked in Phase 1.\n\n"
        "See the finalizer console output for test status.\n",
        encoding="utf-8",
    )

    if args.skip_tests:
        print("[WARNING] Tests skipped; archive is not test-validated.")
    else:
        print("\n[CHECK] Running pytest -q ...")
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=root,
            check=True,
        )

    package(root, Path(args.output))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError,
            zipfile.BadZipFile) as error:
        print(f"\n[ERROR] {error}", file=sys.stderr)
        raise SystemExit(2)
