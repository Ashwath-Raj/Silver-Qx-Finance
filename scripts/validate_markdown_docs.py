#!/usr/bin/env python3
"""Validate project documentation: GitHub math delimiters, local links, result markers."""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", ROOT / "report.md", ROOT / "PROOF_OF_WORK_STATUS.md"]
errors: list[str] = []

def check_text(text: str, label: str) -> None:
    if any(token in text for token in (r"\(", r"\)", r"\[", r"\]")):
        errors.append(f"{label}: use GitHub math delimiters $...$ inline and $$...$$ display.")
    if "\x08" in text or any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        errors.append(f"{label}: contains a control character.")
    if text.count("$$") % 2:
        errors.append(f"{label}: unbalanced $$ display-math delimiters.")
    remaining = re.sub(r"```.*?```", "", text, flags=re.S)
    remaining = re.sub(r"`[^`]*`", "", remaining).replace("$$", "")
    remaining = re.sub(r"\\\$", "", remaining)
    if remaining.count("$") % 2:
        errors.append(f"{label}: unbalanced inline $ math delimiters.")

def internal_target(target: str) -> str | None:
    target = target.strip().strip("<>")
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return unquote(parsed.path)

def check_links(text: str, label: str) -> None:
    for dest in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
        local = internal_target(dest.split()[0])
        if local and not (ROOT / local).exists():
            errors.append(f"{label}: broken Markdown link/image: {dest}")
    for dest in re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", text, re.I):
        local = internal_target(dest)
        if local and not (ROOT / local).exists():
            errors.append(f"{label}: broken HTML image src: {dest}")

for path in DOCS:
    if not path.is_file():
        errors.append(f"Missing documentation: {path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8")
    label = path.relative_to(ROOT).as_posix()
    check_text(text, label)
    check_links(text, label)
    if path.name in {"README.md", "report.md"}:
        for marker in ("<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->"):
            if text.count(marker) != 1:
                errors.append(f"{label}: expected exactly one {marker}")

nbpath = ROOT / "main.ipynb"
if nbpath.is_file():
    try:
        nb = json.loads(nbpath.read_text(encoding="utf-8"))
        for i, cell in enumerate(nb.get("cells", []), 1):
            if cell.get("cell_type") == "markdown":
                s = "".join(cell.get("source", []))
                check_text(s, f"main.ipynb Markdown cell {i}")
                check_links(s, f"main.ipynb Markdown cell {i}")
    except Exception as e:
        errors.append(f"main.ipynb: invalid notebook JSON: {e}")
if errors:
    print("DOCUMENTATION VALIDATION: FAIL")
    for e in errors:
        print("-", e)
    raise SystemExit(1)
print("DOCUMENTATION VALIDATION: PASS")
print("Checked README/report/status, notebook Markdown, GitHub math delimiters, local links and generated-result markers.")
