"""Validate official CICIoT2023 CSV files and record provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ciciot2023_common import ATTACK_GROUPS, filename_label

ML_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ML_ROOT / "data" / "raw" / "ciciot2023" / "CSV"
DEFAULT_OUTPUT = ML_ROOT / "artifacts" / "ciciot2023-dataset-validation.json"
LABEL_COLUMN = "label"
BENIGN_LABEL = "BenignTraffic"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file(path: Path, chunk_size: int, include_hash: bool) -> dict:
    rows = 0
    labels: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    non_finite: Counter[str] = Counter()
    schema: list[str] | None = None
    dtypes: dict[str, str] = {}
    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        if schema is None:
            schema = list(chunk.columns)
            dtypes = {column: str(dtype) for column, dtype in chunk.dtypes.items()}
        elif list(chunk.columns) != schema:
            raise ValueError(f"Schema changed inside {path}")
        rows += len(chunk)
        if LABEL_COLUMN in chunk.columns:
            if chunk[LABEL_COLUMN].isna().any():
                raise ValueError(f"Missing labels in {path}")
            values = chunk[LABEL_COLUMN].dropna().astype(str)
            unknown = set(values) - set(ATTACK_GROUPS)
            if unknown:
                raise ValueError(f"Unknown labels in {path}: {sorted(unknown)}")
            labels.update(values)
        else:
            labels[filename_label(path)] += len(chunk)
        for column, count in chunk.isna().sum().items():
            if count:
                missing[str(column)] += int(count)
        numeric = chunk.select_dtypes(include=[np.number])
        if not numeric.empty:
            counts = np.isinf(numeric.to_numpy()).sum(axis=0)
            for column, count in zip(numeric.columns, counts, strict=True):
                if count:
                    non_finite[str(column)] += int(count)
    return {
        "path": path.resolve().as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path) if include_hash else None,
        "rows": rows,
        "columns": schema or [],
        "dtypes_first_chunk": dtypes,
        "label_counts": dict(sorted(labels.items())),
        "label_source": "column" if LABEL_COLUMN in (schema or []) else "verified filename taxonomy",
        "missing_by_column": dict(sorted(missing.items())),
        "non_finite_by_column": dict(sorted(non_finite.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--skip-hashes", action="store_true")
    args = parser.parse_args()
    files = sorted(args.data_dir.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CICIoT2023 CSV files found under {args.data_dir}. "
            "Download the official CSV directory first."
        )

    reports = []
    reference_schema: list[str] | None = None
    total_labels: Counter[str] = Counter()
    for index, path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] validating {path.name}", flush=True)
        report = validate_file(path, args.chunk_size, not args.skip_hashes)
        if reference_schema is None:
            reference_schema = report["columns"]
        elif report["columns"] != reference_schema:
            raise ValueError(f"Schema mismatch in {path}")
        total_labels.update(report["label_counts"])
        reports.append(report)

    total_rows = sum(report["rows"] for report in reports)
    benign_rows = total_labels.get(BENIGN_LABEL, 0)
    result = {
        "dataset": "CICIoT2023 CSV features",
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "official_source": "https://www.unb.ca/cic/datasets/iotdataset-2023.html",
        "official_download": "https://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/",
        "citation_doi": "https://doi.org/10.3390/s23135941",
        "data_directory": args.data_dir.resolve().as_posix(),
        "hashes_included": not args.skip_hashes,
        "file_count": len(reports),
        "total_rows": total_rows,
        "column_count": len(reference_schema or []),
        "columns": reference_schema or [],
        "label_counts": dict(sorted(total_labels.items())),
        "observed_attack_groups": {name: ATTACK_GROUPS[name] for name in sorted(total_labels)},
        "binary_counts": {"benign": benign_rows, "attack": total_rows - benign_rows},
        "files": reports,
        "quality_notes": {
            "exact_duplicate_scan": "not performed by this streaming validator",
            "split_status": "not created; freeze split only after provenance audit",
            "binary_mapping": f"{BENIGN_LABEL}=0; documented attack labels=1",
            "format_note": "This release may encode labels in per-attack .pcap.csv filenames. Labels are never input features.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Validated {len(reports)} files and {total_rows} rows; saved {args.output}")


if __name__ == "__main__":
    main()
