#!/usr/bin/env python3
"""Generate deterministic healthy Vendor A training/holdout data."""
from __future__ import annotations

import argparse

from creditscore.data.generator import SyntheticDataConfig, generate_lending_dataset
from creditscore.data.loader import split_train_holdout
from creditscore.utils.config import load_config, project_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    root = project_root()

    data_cfg = SyntheticDataConfig(
        n_samples=int(cfg["data"]["n_samples"]),
        random_seed=int(cfg["project"]["random_seed"]),
        baseline_device_null_rate=float(cfg["data"]["baseline_device_null_rate"]),
    )
    frame = generate_lending_dataset(data_cfg)
    train, holdout = split_train_holdout(
        frame,
        target_column=cfg["data"]["target_column"],
        test_size=float(cfg["data"]["test_size"]),
        random_state=int(cfg["project"]["random_seed"]),
    )

    out = root / "data" / "raw" / "vendor_a"
    out.mkdir(parents=True, exist_ok=True)
    train.to_csv(out / "train.csv", index=False)
    holdout.to_csv(out / "holdout.csv", index=False)
    print(f"Generated Vendor A: train={len(train):,}, holdout={len(holdout):,}")
    print(f"Holdout device_risk_score NULL rate={holdout['device_risk_score'].isna().mean():.3%}")


if __name__ == "__main__":
    main()
