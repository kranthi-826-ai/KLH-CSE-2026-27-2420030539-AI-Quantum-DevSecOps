"""Diagnose Random Forest validation errors without opening official test data."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pandas as pd
from sklearn.model_selection import train_test_split

from train_baselines import ARTIFACT_DIR, EXCLUDED, FILES, SEED, metrics, models, sha256

RUN_ID = "random-forest-validation-error-analysis-v1"


def grouped_error(frame: pd.DataFrame, column: str, *, false_positives: bool) -> list[dict]:
    subset = frame[frame["label"] == 0] if false_positives else frame[frame["label"] == 1]
    rows = []
    for value, group in subset.groupby(column, dropna=False):
        total = int(len(group))
        errors = int((group["prediction"] != group["label"]).sum())
        rows.append({
            column: str(value),
            "samples": total,
            "errors": errors,
            "error_rate": float(errors / total) if total else 0.0,
        })
    return sorted(rows, key=lambda item: (-item["errors"], -item["samples"], item[column]))


def main() -> None:
    source, expected_rows = FILES["training"]
    data = pd.read_csv(source)
    if len(data) != expected_rows:
        raise ValueError("Unexpected training row count; validate UNSW-NB15 first")
    fit, validation = train_test_split(
        data, test_size=0.20, stratify=data["label"], random_state=SEED,
    )
    feature_names = [column for column in data.columns if column not in EXCLUDED]
    model = models(feature_names)["random_forest"]
    started = time.perf_counter()
    model.fit(fit[feature_names], fit["label"].astype(int))
    training_seconds = time.perf_counter() - started
    predictions = model.predict(validation[feature_names])
    scored = validation[["label", "attack_cat", "proto", "service", "state"]].copy()
    scored["prediction"] = predictions
    transformed_names = model.named_steps["preprocess"].get_feature_names_out()
    importances = model.named_steps["model"].feature_importances_
    ranked_features = sorted(
        ({"feature": str(name), "importance": float(value)}
         for name, value in zip(transformed_names, importances, strict=True)),
        key=lambda item: item["importance"], reverse=True,
    )
    report = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "official training CSV only; fixed stratified 80/20 split; official test not loaded",
        "seed": SEED,
        "training_sha256": sha256(source),
        "split": {"fit": len(fit), "validation": len(validation)},
        "training_seconds": training_seconds,
        "overall_validation": metrics(model, validation[feature_names], validation["label"].astype(int)),
        "attack_family_errors": grouped_error(scored, "attack_cat", false_positives=False),
        "false_positives_by_protocol": grouped_error(scored, "proto", false_positives=True),
        "false_positives_by_service": grouped_error(scored, "service", false_positives=True),
        "false_positives_by_state": grouped_error(scored, "state", false_positives=True),
        "top_feature_importance": ranked_features[:30],
        "interpretation": "Diagnostic evidence only; no official-test data was loaded and no model was promoted.",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_DIR / f"{RUN_ID}.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}")
    for item in report["attack_family_errors"]:
        print(f"{item['attack_cat']}: missed={item['errors']}/{item['samples']} ({item['error_rate']:.2%})")
    print("Top validation false-positive groups:")
    for dimension in ("false_positives_by_protocol", "false_positives_by_service", "false_positives_by_state"):
        print(dimension, report[dimension][:5])


if __name__ == "__main__":
    main()
