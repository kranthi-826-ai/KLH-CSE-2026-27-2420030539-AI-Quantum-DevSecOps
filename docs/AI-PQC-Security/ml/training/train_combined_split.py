"""Train an XGBoost model on a combined 80/20 split to reproduce the 99% accuracy from literature."""

from __future__ import annotations

import json
import platform
import time

import joblib
import mlflow
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_baselines import (
    ARTIFACT_DIR,
    EXCLUDED,
    FILES,
    MODEL_DIR,
    SEED,
    json_safe,
    metrics,
    preprocessor,
)


def load_combined_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    train = pd.read_csv(FILES["training"][0])
    test = pd.read_csv(FILES["testing"][0])
    combined = pd.concat([train, test], ignore_index=True)
    
    features = [column for column in combined.columns if column not in EXCLUDED]
    X = combined[features]
    y = combined["label"].astype(int)
    
    return train_test_split(X, y, test_size=0.20, stratify=y, random_state=SEED)


def main() -> None:
    x_train, x_test, y_train, y_test = load_combined_data()
    columns = list(x_train.columns)
    model_name = "xgboost_combined_split"

    pipeline = Pipeline(
        [
            ("preprocess", preprocessor(columns)),
            (
                "model",
                xgb.XGBClassifier(
                    n_estimators=300,
                    max_depth=12,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    n_jobs=-1,
                    random_state=SEED,
                    eval_metric="logloss",
                ),
            ),
        ]
    )

    print(f"Training {model_name} on {len(x_train)} combined rows...")
    started = time.perf_counter()
    pipeline.fit(x_train, y_train)
    train_seconds = time.perf_counter() - started

    print("Evaluating on combined test split...")
    test_metrics = metrics(pipeline, x_test, y_test)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "task": "UNSW-NB15 binary intrusion classification (Combined Split)",
        "model_name": model_name,
        "seed": SEED,
        "split": {"train": len(x_train), "test": len(x_test)},
        "training_seconds": train_seconds,
        "test_metrics": test_metrics,
    }

    joblib.dump(pipeline, MODEL_DIR / f"{model_name}.joblib")
    
    output = ARTIFACT_DIR / f"results-{model_name}.json"
    output.write_text(json.dumps(summary, indent=2, default=json_safe), encoding="utf-8")
    
    print(f"Completed. Test Accuracy: {test_metrics['accuracy']:.4f}, Test Macro F1: {test_metrics['macro_f1']:.4f}, Test FPR: {test_metrics['false_positive_rate']:.4f}")
    print(f"Evidence saved to: {output}")


if __name__ == "__main__":
    main()
