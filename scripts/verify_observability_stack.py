#!/usr/bin/env python3
"""Verify the local API, Prometheus, and Grafana observability stack."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any


def _read_text(url: str, *, timeout_seconds: float = 3.0) -> str:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8")


def _wait_for(
    name: str,
    url: str,
    predicate: Callable[[str], bool],
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            body = _read_text(url)
            if predicate(body):
                print(f"{name}: healthy")
                return
            last_error = RuntimeError(f"{name} returned an unexpected response")
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
            RuntimeError,
        ) as exc:
            last_error = exc
        time.sleep(1)

    raise RuntimeError(f"{name} did not become healthy: {last_error}")


def _json_field(expected_key: str, expected_value: Any) -> Callable[[str], bool]:
    def predicate(body: str) -> bool:
        payload = json.loads(body)
        return payload.get(expected_key) == expected_value

    return predicate


def _prometheus_target_is_up() -> bool:
    query = urllib.parse.urlencode({"query": 'up{job="creditscorev4-api"}'})
    payload = json.loads(_read_text(f"http://127.0.0.1:9090/api/v1/query?{query}"))
    if payload.get("status") != "success":
        return False
    results = payload.get("data", {}).get("result", [])
    return any(
        str(item.get("metric", {}).get("instance")) == "api:8000"
        and len(item.get("value", [])) == 2
        and float(item["value"][1]) == 1.0
        for item in results
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    args = parser.parse_args()

    _wait_for(
        "CreditScoreV4 API",
        "http://127.0.0.1:8000/health",
        _json_field("status", "ok"),
        timeout_seconds=args.timeout_seconds,
    )
    _wait_for(
        "Prometheus",
        "http://127.0.0.1:9090/-/healthy",
        lambda body: "Prometheus Server is Healthy" in body,
        timeout_seconds=args.timeout_seconds,
    )
    _wait_for(
        "Grafana",
        "http://127.0.0.1:3000/api/health",
        _json_field("database", "ok"),
        timeout_seconds=args.timeout_seconds,
    )

    deadline = time.monotonic() + args.timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if _prometheus_target_is_up():
                print('Prometheus scrape: up{job="creditscorev4-api"} = 1')
                return 0
            last_error = RuntimeError("CreditScoreV4 target is not up yet")
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(1)

    raise RuntimeError(f"Prometheus did not report the API target as up: {last_error}")


if __name__ == "__main__":
    raise SystemExit(main())
