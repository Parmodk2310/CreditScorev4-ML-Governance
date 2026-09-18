"""Deterministic request routing for canary traffic."""

from __future__ import annotations

import hashlib


class CanaryRouter:
    def __init__(self, share: float) -> None:
        self.set_share(share)

    @property
    def share(self) -> float:
        return self._share

    def set_share(self, share: float) -> None:
        share = float(share)
        if not 0.0 <= share <= 1.0:
            raise ValueError("Canary share must be between 0 and 1")
        self._share = share

    @staticmethod
    def bucket(request_key: str) -> float:
        digest = hashlib.sha256(str(request_key).encode("utf-8")).digest()
        integer = int.from_bytes(digest[:8], byteorder="big", signed=False)
        return integer / float(2**64)

    def route(self, request_key: str) -> str:
        if self._share >= 1.0:
            return "candidate"
        return "candidate" if self.bucket(request_key) < self._share else "baseline"
