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
ARCHITECTURE = ROOT / "ARCHITECTURE.md"

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

PRIMARY_SYSTEM_DIAGRAMS = (
    "system-overview",
    "governance-release-model",
    "delivery-controls",
)

PHASE8_13 = REQUIRED[7:13]

SUPPLEMENTAL = (
    "phase1-7-end-to-end",
    "release-state",
)


def fail(message: str) -> None:
    raise ValueError(message)


def validate_mermaid(path: Path, *, strict: bool) -> None:
    text = path.read_text(encoding="utf-8")

    first = next(
        (line.strip() for line in text.splitlines() if line.strip()),
        "",
    )

    if strict:
        if not first.startswith("flowchart "):
            fail(f"{path}: current architecture must start " "with a Mermaid flowchart declaration")
    else:
        supported = first.startswith("flowchart ") or first == "stateDiagram-v2"
        if not supported:
            fail(f"{path}: unsupported Mermaid declaration {first!r}")

    if strict:
        if "|" in text:
            fail(f"{path}: raw pipe character is not allowed " "in current Mermaid architecture sources")

        if r"\n" in text:
            fail(f"{path}: use <br/> rather than literal " r"Mermaid \n label escapes")

        if '["' not in text or '"]' not in text:
            fail(f"{path}: current node labels must use " "quoted Mermaid text")


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
            capture_output=True,
            text=True,
        )
        ET.parse(tmp.name)


def validate_phase_set(stem: str, *, strict_mermaid: bool) -> None:
    mmd = DIAGRAM_DIR / f"{stem}.mmd"
    dot = DIAGRAM_DIR / f"{stem}.dot"
    svg = DIAGRAM_DIR / f"{stem}.svg"

    for path in (mmd, dot, svg):
        if not path.exists():
            fail(f"Missing architecture artifact: {path}")

    validate_mermaid(mmd, strict=strict_mermaid)
    validate_dot(dot)
    validate_svg(svg)
    render_dot_if_available(dot)


def validate_system_set(stem: str) -> None:
    mmd = DIAGRAM_DIR / f"{stem}.mmd"
    svg = DIAGRAM_DIR / f"{stem}.svg"

    for path in (mmd, svg):
        if not path.exists():
            fail(f"Missing primary architecture artifact: {path}")

    validate_mermaid(mmd, strict=True)
    validate_svg(svg)


def main() -> int:
    figure_index = FIGURE_INDEX.read_text(encoding="utf-8")
    phase8_13_index = PHASE8_13_INDEX.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")

    for stem in PRIMARY_SYSTEM_DIAGRAMS:
        validate_system_set(stem)

        for document, document_text in (
            (FIGURE_INDEX, figure_index),
            (README, readme),
            (ARCHITECTURE, architecture),
        ):
            if stem not in document_text:
                fail(f"{document}: missing primary architecture reference for {stem}")

        print(f"PRIMARY DIAGRAM VALID: {stem}")

    for stem in REQUIRED:
        validate_phase_set(
            stem,
            strict_mermaid=True,
        )

        if stem not in figure_index:
            fail(f"{FIGURE_INDEX}: missing architecture entry for {stem}")

        print(f"DIAGRAM VALID: {stem}")

    for stem in PHASE8_13:
        if stem not in phase8_13_index:
            fail(f"{PHASE8_13_INDEX}: missing architecture entry for {stem}")

    for stem in SUPPLEMENTAL:
        mmd = DIAGRAM_DIR / f"{stem}.mmd"
        dot = DIAGRAM_DIR / f"{stem}.dot"
        svg = DIAGRAM_DIR / f"{stem}.svg"

        existing = (
            mmd.exists(),
            dot.exists(),
            svg.exists(),
        )

        if any(existing) and not all(existing):
            fail(f"{stem}: supplemental diagram set is incomplete")

        if all(existing):
            validate_phase_set(
                stem,
                strict_mermaid=False,
            )
            print(f"SUPPLEMENTAL DIAGRAM VALID: {stem}")

    renderer = shutil.which("dot")

    if renderer:
        print(f"Graphviz phase-diagram render check: PASS ({renderer})")
    else:
        print(
            "Graphviz phase-diagram render check: SKIPPED "
            "(dot not installed); committed SVG/XML validation passed"
        )

    print(
        f"Validated {len(PRIMARY_SYSTEM_DIAGRAMS)} primary system diagrams, "
        f"{len(REQUIRED)} current phase architecture sets, "
        "and available supplemental diagrams."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
