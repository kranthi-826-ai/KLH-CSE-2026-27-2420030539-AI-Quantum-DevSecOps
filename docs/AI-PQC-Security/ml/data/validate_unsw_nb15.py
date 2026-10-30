"""Validate official UNSW-NB15 predefined files and record provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ML_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ML_ROOT.parent
DATA_DIR = ML_ROOT / "data" / "raw" / "unsw-nb15"
OUTPUT = ML_ROOT / "artifacts" / "dataset-validation.json"
FILES = {
    "training": (DATA_DIR / "UNSW_NB15_training-set.csv", 175_341),
    "testing": (DATA_DIR / "UNSW_NB15_testing-set.csv", 82_332),
}
REQUIRED_COLUMNS = {"id", "proto", "service", "state", "attack_cat", "label"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(path: Path, expected_rows: int) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Missing official dataset file: {path}")
    frame = pd.read_csv(path)
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"{path.name} is missing columns: {missing_columns}")
    if len(frame) != expected_rows:
        raise ValueError(
            f"{path.name} has {len(frame):,} rows; expected {expected_rows:,}"
        )
    labels = pd.to_numeric(frame["label"], errors="raise")
    if not set(labels.unique()).issubset({0, 1}):
        raise ValueError(f"{path.name} label must contain only 0 and 1")
    return {
        "path": str(path.relative_to(REPOSITORY_ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": len(frame),
        "columns": list(frame.columns),
        "dtypes": {name: str(dtype) for name, dtype in frame.dtypes.items()},
        "missing_by_column": {
            name: int(value) for name, value in frame.isna().sum().items()
        },
        "duplicate_rows": int(frame.duplicated().sum()),
        "binary_label_counts": {
            str(key): int(value) for key, value in labels.value_counts().sort_index().items()
        },
        "attack_category_counts": {
            str(key): int(value)
            for key, value in frame["attack_cat"].fillna("Normal").value_counts().items()
        },
    }


def main() -> None:
    report = {
        "dataset": "UNSW-NB15 official predefined split",
        "source": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "files": {
            name: inspect_file(path, rows) for name, (path, rows) in FILES.items()
        },
    }
    train_columns = report["files"]["training"]["columns"]
    test_columns = report["files"]["testing"]["columns"]
    if train_columns != test_columns:
        raise ValueError("Training and testing schemas differ")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Dataset validation passed. Evidence: {OUTPUT}")


if __name__ == "__main__":
    main()
