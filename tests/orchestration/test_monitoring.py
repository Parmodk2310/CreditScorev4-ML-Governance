from __future__ import annotations

from pathlib import Path

import pytest

from creditscore.orchestration import (
    MonitoringOrchestrator,
    MonitoringTaskSpec,
    load_task_specs,
    topological_order,
    validate_task_graph,
)


def _config(tasks: list[dict]) -> dict:
    return {
        "orchestration": {
            "fail_closed": True,
            "automatic_retraining": False,
            "automatic_promotion": False,
            "tasks": tasks,
        },
        "execution": {
            "max_attempts": 1,
            "retry_delay_seconds": 0,
        },
    }


def test_task_graph_orders_dependencies() -> None:
    specs = [
        MonitoringTaskSpec("second", ("python", "-c", "pass"), ("first",)),
        MonitoringTaskSpec("first", ("python", "-c", "pass")),
    ]

    ordered = topological_order(specs)
    assert [spec.task_id for spec in ordered] == ["first", "second"]


def test_task_graph_rejects_cycles() -> None:
    specs = [
        MonitoringTaskSpec("a", ("python", "-c", "pass"), ("b",)),
        MonitoringTaskSpec("b", ("python", "-c", "pass"), ("a",)),
    ]

    with pytest.raises(ValueError, match="cycle"):
        validate_task_graph(specs)


def test_failed_task_skips_dependent_task(tmp_path: Path) -> None:
    marker = tmp_path / "should-not-exist.txt"
    config = _config(
        [
            {
                "id": "fail",
                "command": ["python", "-c", "import sys; sys.exit(3)"],
            },
            {
                "id": "dependent",
                "depends_on": ["fail"],
                "command": [
                    "python",
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')",
                ],
            },
        ]
    )

    run = MonitoringOrchestrator(root=tmp_path, config=config).run(
        run_id="test-fail-closed",
        source_commit="test",
    )

    assert run.final_status == "FAIL"
    assert run.tasks[0].status == "FAIL"
    assert run.tasks[1].status == "SKIPPED"
    assert not marker.exists()


def test_missing_expected_evidence_fails_task(tmp_path: Path) -> None:
    config = _config(
        [
            {
                "id": "missing",
                "command": ["python", "-c", "pass"],
                "evidence": ["evidence.json"],
            }
        ]
    )

    run = MonitoringOrchestrator(root=tmp_path, config=config).run(
        run_id="test-missing-evidence",
        source_commit="test",
    )

    assert run.final_status == "FAIL"
    assert run.tasks[0].status == "FAIL"
    assert "expected evidence missing" in run.tasks[0].reason


def test_successful_task_hashes_evidence(tmp_path: Path) -> None:
    config = _config(
        [
            {
                "id": "write",
                "command": [
                    "python",
                    "-c",
                    "from pathlib import Path; Path('evidence.json').write_text('ok')",
                ],
                "evidence": ["evidence.json"],
            }
        ]
    )

    run = MonitoringOrchestrator(root=tmp_path, config=config).run(
        run_id="test-success",
        source_commit="test",
    )

    assert run.final_status == "PASS"
    assert run.tasks[0].status == "PASS"
    digest = run.tasks[0].evidence_sha256["evidence.json"]
    assert len(digest) == 64


def test_config_loader_uses_default_attempts() -> None:
    config = _config([{"id": "one", "command": ["python", "-c", "pass"]}])
    config["execution"]["max_attempts"] = 2

    specs = load_task_specs(config)

    assert specs[0].max_attempts == 2
