"""Measure feature drift without mixing runtime events into training data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

EPSILON = 1e-6


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    reference = pd.to_numeric(reference, errors="coerce").dropna()
    current = pd.to_numeric(current, errors="coerce").dropna()
    if reference.empty or current.empty:
        return 0.0
    edges = np.unique(reference.quantile(np.linspace(0, 1, bins + 1)).to_numpy())
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    expected = np.histogram(reference, bins=edges)[0] / len(reference)
    actual = np.histogram(current, bins=edges)[0] / len(current)
    expected = np.clip(expected, EPSILON, None)
    actual = np.clip(actual, EPSILON, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def categorical_total_variation(reference: pd.Series, current: pd.Series) -> float:
    categories = reference.astype(str).value_counts(normalize=True).index.union(
        current.astype(str).value_counts(normalize=True).index
    )
    expected = reference.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    actual = current.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    return float(0.5 * np.abs(expected - actual).sum())


def drift_report(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    shared = sorted(set(reference.columns).intersection(current.columns))
    features = {}
    for column in shared:
        if pd.api.types.is_numeric_dtype(reference[column]):
            score = population_stability_index(reference[column], current[column])
            method, threshold = "psi", 0.20
        else:
            score = categorical_total_variation(reference[column], current[column])
            method, threshold = "total_variation", 0.20
        features[column] = {
            "method": method,
            "score": score,
            "threshold": threshold,
            "drifted": score >= threshold,
        }
    drifted = sorted(name for name, value in features.items() if value["drifted"])
    return {
        "reference_rows": len(reference),
        "current_rows": len(current),
        "shared_features": len(shared),
        "drifted_features": drifted,
        "drift_detected": bool(drifted),
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("ml/artifacts/drift-report.json"))
    args = parser.parse_args()
    report = drift_report(pd.read_csv(args.reference), pd.read_csv(args.current))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Drift detected: {report['drift_detected']}; report: {args.output}")


if __name__ == "__main__":
    main()
