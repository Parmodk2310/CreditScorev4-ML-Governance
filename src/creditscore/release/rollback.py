"""Rollback reason formatting kept separate from transition mechanics."""

from __future__ import annotations

from .models import ReleaseGateResult


def rollback_reason(results: list[ReleaseGateResult]) -> str:
    failures = [result.name for result in results if not result.passed]
    if not failures:
        return "manual rollback"
    return "release gates failed: " + ", ".join(sorted(failures))
