#!/usr/bin/env python3
"""Validate CreditScoreV4 architecture sources and rendered assets."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = ROOT / "docs" / "assets" / "diagrams"
FIGURE_INDEX = ROOT / "docs" / "ARCHITECTURE_FIGURES.md"
PHASE8_13_INDEX = ROOT / "docs" / "PHASE8_13_ARCHITECTURE.md"
README = ROOT / "README.md"

REQUIRED = (
    "phase1-incident-baseline",
    "phase2-data-quality-governance",
    "phase3-drift-governance",
    "phase4-fairness-explainability",
    "phase5-governance-registry",
    "phase6-serving-safe-release",
    "phase7-automation-deployment",
    "phase8-governance-evidence",
    "phase9-business-impact",
    "phase10-root-cause",
    "phase11-orchestration",
    "phase12-fairness-proxy",
    "phase13-incident-ops",
    "phase1-13-end-to-end",
)

PHASE8_13 = REQUIRED[7:13]


def fail(message: str) -> None:
    raise ValueError(message)


def validate_mermaid(path: Path, *, strict: bool) -> None:
    text = path.read_text(encoding="utf-8")
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first.startswith("flowchart "):
        fail(f"{path}: expected Mermaid flowchart declaration")

    if strict:
        if "|" in text:
            fail(f"{path}: raw pipe character is not allowed in recreated Mermaid sources")
        if r"\n" in text:
            fail(f"{path}: use <br/> instead of literal Mermaid \\n label escapes")
        if '["' not in text or '"]' not in text:
            fail(f"{path}: recreated node labels must use quoted text")


def validate_dot(path: Path) -> None:
    text = path.read_text(encoding="utf-8").strip()
    if not text.startswith("digraph "):
        fail(f"{path}: expected Graphviz digraph")
    if text.count("{") != text.count("}"):
        fail(f"{path}: unbalanced Graphviz braces")


def validate_svg(path: Path) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        fail(f"{path}: invalid SVG/XML: {exc}")
    if not root.tag.endswith("svg"):
        fail(f"{path}: root element is not SVG")


def render_dot_if_available(path: Path) -> None:
    dot = shutil.which("dot")
    if dot is None:
        return
    with tempfile.NamedTemporaryFile(suffix=".svg") as tmp:
        subprocess.run(
            [dot, "-Tsvg", str(path), "-o", tmp.name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        ET.parse(tmp.name)


def main() -> int:
    figure_index = FIGURE_INDEX.read_text(encoding="utf-8")
    phase8_13_index = PHASE8_13_INDEX.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    for stem in REQUIRED:
        mmd = DIAGRAM_DIR / f"{stem}.mmd"
        dot = DIAGRAM_DIR / f"{stem}.dot"
        svg = DIAGRAM_DIR / f"{stem}.svg"

        for path in (mmd, dot, svg):
            if not path.exists():
                fail(f"Missing architecture artifact: {path}")

        validate_mermaid(mmd, strict=True)
        validate_dot(dot)
        validate_svg(svg)
        render_dot_if_available(dot)

        if stem not in figure_index:
            fail(f"{FIGURE_INDEX}: missing architecture entry for {stem}")

        print(f"DIAGRAM VALID: {stem}")

    for stem in PHASE8_13:
        if stem not in phase8_13_index:
            fail(f"{PHASE8_13_INDEX}: missing architecture entry for {stem}")

    for stem in ("phase1-7-end-to-end", "release-state"):
        mmd = DIAGRAM_DIR / f"{stem}.mmd"
        dot = DIAGRAM_DIR / f"{stem}.dot"
        svg = DIAGRAM_DIR / f"{stem}.svg"
        if all(path.exists() for path in (mmd, dot, svg)):
            validate_mermaid(mmd, strict=False)
            validate_dot(dot)
            validate_svg(svg)
            render_dot_if_available(dot)
            print(f"SUPPLEMENTAL DIAGRAM VALID: {stem}")

    if "docs/assets/diagrams/phase1-13-end-to-end.svg" not in readme:
        fail("README.md: current overview must reference phase1-13-end-to-end.svg")

    renderer = shutil.which("dot")
    if renderer:
        print(f"Graphviz render check: PASS ({renderer})")
    else:
        print("Graphviz render check: SKIPPED (dot not installed); committed SVG/XML validation passed")

    print(f"Validated {len(REQUIRED)} current architecture diagram sets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
