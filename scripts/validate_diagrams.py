#!/usr/bin/env python3
"""Validate architecture diagram source and rendered-artifact contracts."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = ROOT / "docs" / "assets" / "diagrams"
ARCHITECTURE_INDEX = ROOT / "docs" / "PHASE8_13_ARCHITECTURE.md"

STEMS = (
    "phase8-governance-evidence",
    "phase9-business-impact",
    "phase10-root-cause",
    "phase11-orchestration",
    "phase12-fairness-proxy",
    "phase13-incident-ops",
)

NODE_PATTERN = re.compile(r"\\b[A-Za-z_][A-Za-z0-9_]*\\[([^\\]]*)\\]")


def fail(message: str) -> None:
    raise ValueError(message)


def validate_mermaid(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    first_line = next(
        (line.strip() for line in text.splitlines() if line.strip()),
        "",
    )

    if first_line not in {"flowchart LR", "flowchart TB"}:
        fail(f"{path}: unsupported or missing flowchart declaration")

    # This repository intentionally uses a conservative Mermaid subset.
    # Raw pipes caused the GitHub Phase 12 rendering regression.
    if "|" in text:
        fail(f"{path}: raw '|' is not allowed in Mermaid labels")

    # Use <br/> rather than backslash-newline label escapes.
    if "\\n" in text:
        fail(f"{path}: use <br/> instead of Mermaid label \\n escapes")

    for match in NODE_PATTERN.finditer(text):
        label = match.group(1).strip()
        if not (label.startswith('"') and label.endswith('"')):
            fail(f"{path}: node labels must use quoted Mermaid text: " f"[{label}]")


def validate_dot(path: Path, phase: int) -> None:
    text = path.read_text(encoding="utf-8").strip()

    if not text.startswith(f"digraph Phase{phase}"):
        fail(f"{path}: unexpected Graphviz graph declaration")

    if text.count("{") != text.count("}"):
        fail(f"{path}: unbalanced Graphviz braces")


def validate_svg(path: Path) -> None:
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        fail(f"{path}: invalid SVG/XML: {exc}")

    root = tree.getroot()

    if not root.tag.endswith("svg"):
        fail(f"{path}: root element is not SVG")


def main() -> int:
    architecture = ARCHITECTURE_INDEX.read_text(encoding="utf-8")

    for phase, stem in enumerate(STEMS, start=8):
        mermaid = DIAGRAM_DIR / f"{stem}.mmd"
        dot = DIAGRAM_DIR / f"{stem}.dot"
        svg = DIAGRAM_DIR / f"{stem}.svg"

        for path in (mermaid, dot, svg):
            if not path.exists():
                fail(f"Missing diagram artifact: {path}")

        validate_mermaid(mermaid)
        validate_dot(dot, phase)
        validate_svg(svg)

        relative_svg = f"assets/diagrams/{stem}.svg"
        if relative_svg not in architecture:
            fail(f"{ARCHITECTURE_INDEX}: missing reference to " f"{relative_svg}")

        print(f"DIAGRAM VALID: {stem}")

    print(f"Validated {len(STEMS)} Phase 8-13 diagram sets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
