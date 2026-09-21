from importlib.metadata import version

from creditscore import __version__


def test_runtime_version_matches_package_metadata() -> None:
    assert __version__ == version("creditscorev4-ml-governance")