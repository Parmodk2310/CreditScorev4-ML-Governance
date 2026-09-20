from __future__ import annotations

from pathlib import Path

from creditscore.orchestration import MonitoringOrchestrator


def test_phase11_orchestrator_records_order_and_fail_closed_state(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    config = {
        "orchestration": {
            "fail_closed": True,
            "automatic_retraining": False,
            "automatic_promotion": False,
            "tasks": [
                {
                    "id": "first",
                    "command": [
                        "python",
                        "-c",
                        "from pathlib import Path; Path('first.json').write_text('one')",
                    ],
                    "evidence": ["first.json"],
                },
                {
                    "id": "second",
                    "depends_on": ["first"],
                    "command": [
                        "python",
                        "-c",
                        "from pathlib import Path; Path('second.json').write_text('two')",
                    ],
                    "evidence": ["second.json"],
                },
            ],
        },
        "execution": {
            "max_attempts": 1,
            "retry_delay_seconds": 0,
        },
    }

    run = MonitoringOrchestrator(root=tmp_path, config=config).run(
        run_id="integration",
        source_commit="abc123",
    )

    assert first.exists()
    assert second.exists()
    assert run.final_status == "PASS"
    assert [task.task_id for task in run.tasks] == ["first", "second"]
    assert [task.status for task in run.tasks] == ["PASS", "PASS"]
    assert run.fail_closed is True
    assert run.automatic_retraining is False
    assert run.automatic_promotion is False
