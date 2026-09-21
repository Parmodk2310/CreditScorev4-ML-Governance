"""CreditScoreV4 ML Governance package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("creditscorev4-ml-governance")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0+unknown"
