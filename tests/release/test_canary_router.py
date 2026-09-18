from creditscore.release.router import CanaryRouter


def test_canary_router_is_deterministic_and_tracks_share() -> None:
    router = CanaryRouter(0.25)
    keys = [f"request-{index}" for index in range(4000)]
    first = [router.route(key) for key in keys]
    second = [router.route(key) for key in keys]
    observed = sum(value == "candidate" for value in first) / len(first)

    assert first == second
    assert 0.22 <= observed <= 0.28
