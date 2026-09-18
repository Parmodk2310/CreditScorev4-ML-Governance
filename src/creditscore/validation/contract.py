"""Load and expose the versioned Phase 2 data contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DataContract:
    name: str
    version: str
    allow_extra_columns: bool
    minimum_rows: int
    columns: dict[str, dict[str, Any]]

    @property
    def required_columns(self) -> list[str]:
        return [name for name, spec in self.columns.items() if bool(spec.get("required", False))]


def load_data_contract(path: str | Path) -> DataContract:
    contract_path = Path(path)
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    header = payload["contract"]
    return DataContract(
        name=str(header["name"]),
        version=str(header["version"]),
        allow_extra_columns=bool(header.get("allow_extra_columns", True)),
        minimum_rows=int(header.get("minimum_rows", 1)),
        columns=dict(payload["columns"]),
    )
