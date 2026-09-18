from creditscore.release.gates import ReleaseGateEvaluator, ReleasePolicy
from creditscore.release.models import ReleaseHealthSnapshot

POLICY = ReleasePolicy(
    maximum_error_rate=0.03,
    maximum_p95_latency_ms=300.0,
    maximum_mean_risk_delta=0.06,
    minimum_request_count=100,
)


def test_release_gates_pass_healthy_snapshot() -> None:
    evaluator = ReleaseGateEvaluator(POLICY)
    assert evaluator.passes(ReleaseHealthSnapshot(500, 0.005, 60.0, 0.01))


def test_release_gates_reject_degraded_snapshot() -> None:
    evaluator = ReleaseGateEvaluator(POLICY)
    results = evaluator.evaluate(ReleaseHealthSnapshot(500, 0.08, 450.0, 0.12))
    failed = {result.name for result in results if not result.passed}
    assert failed == {"error_rate", "p95_latency_ms", "mean_risk_delta"}
