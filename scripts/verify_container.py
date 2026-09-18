#!/usr/bin/env python3
"""Smoke-test either a local Docker image or an already deployed Phase 6 API."""

from __future__ import annotations

import argparse
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import suppress

ENDPOINTS = ("/health", "/ready", "/model")


def wait_for_api(base_url: str, timeout_seconds: int = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=3) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def verify(base_url: str) -> None:
    for endpoint in ENDPOINTS:
        with urllib.request.urlopen(f"{base_url}{endpoint}", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"{endpoint} returned {response.status}")
            print(f"{endpoint}: {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image")
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if bool(args.image) == bool(args.base_url):
        parser.error("provide exactly one of --image or --base-url")

    container_id: str | None = None
    base_url = args.base_url
    try:
        if args.image:
            result = subprocess.run(
                ["docker", "run", "-d", "-p", "8000:8000", args.image],
                capture_output=True,
                text=True,
                check=True,
            )
            container_id = result.stdout.strip()
            base_url = "http://127.0.0.1:8000"
        assert base_url is not None
        wait_for_api(base_url)
        verify(base_url)
    finally:
        if container_id:
            with suppress(subprocess.CalledProcessError):
                subprocess.run(["docker", "rm", "-f", container_id], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
