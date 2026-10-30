"""Train an XGBoost model with feature selection to achieve high generalization."""

from __future__ import annotations

import argparse
import json
import platform
import time

import joblib
import mlflow
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.pipeline import Pipeline

from train_baselines import (
    ARTIFACT_DIR,
    CATEGORICAL,
    EXCLUDED,
    FILES,
    MODEL_DIR,
    SEED,
    json_safe,
    load_data,
    metrics,
    preprocessor,
    sha256,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop-ttl", action="store_true", help="Drop TTL features that cause data leakage")
    args = parser.parse_args()

    x_train, y_train, x_test, y_test = load_data()

    # Drop TTL features if requested to prevent overfitting to the synthetic testbed topology
    dropped_features = list(EXCLUDED)
    if args.drop_ttl:
        ttl_features = ["sttl", "dttl", "ct_state_ttl"]
        x_train = x_train.drop(columns=[col for col in ttl_features if col in x_train.columns], errors="ignore")
        x_test = x_test.drop(columns=[col for col in ttl_features if col in x_test.columns], errors="ignore")
        dropped_features.extend(ttl_features)

    columns = list(x_train.columns)

    model_name = "xgboost_optimized" + ("_no_ttl" if args.drop_ttl else "")
    pipeline = Pipeline(
        [
            ("preprocess", preprocessor(columns)),
            (
                "model",
                xgb.XGBClassifier(
                    n_estimators=300,
                    max_depth=8,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    scale_pos_weight=1.5,  # slight weight for attacks since they are minority in training
                    n_jobs=-1,
                    random_state=SEED,
                    eval_metric="logloss",
                ),
            ),
        ]
    )

    print(f"Training {model_name} with {len(columns)} features...")
    started = time.perf_counter()
    pipeline.fit(x_train, y_train)
    train_seconds = time.perf_counter() - started

    print("Evaluating on test set...")
    test_metrics = metrics(pipeline, x_test, y_test)

    # We also evaluate on training set just for reference to check overfitting
    train_metrics = metrics(pipeline, x_train, y_train)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "task": "UNSW-NB15 binary intrusion classification (XGBoost)",
        "model_name": model_name,
        "seed": SEED,
        "dropped_features": dropped_features,
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgb.__version__,
        },
        "dataset_sha256": {name: sha256(path) for name, (path, _) in FILES.items()},
        "split": {"train": len(x_train), "test": len(x_test)},
        "training_seconds": train_seconds,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
    }

    joblib.dump(pipeline, MODEL_DIR / f"{model_name}.joblib")
    
    # Log to MLflow
    database_path = ARTIFACT_DIR.parent / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{database_path.as_posix()}")
    mlflow.set_experiment("ai-pqc-unsw-nb15")
    with mlflow.start_run(run_name=model_name):
        mlflow.log_params({"model": model_name, "drop_ttl": args.drop_ttl, "seed": SEED})
        mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items() if isinstance(v, (int, float))})

    output = ARTIFACT_DIR / f"results-{model_name}.json"
    output.write_text(json.dumps(summary, indent=2, default=json_safe), encoding="utf-8")
    
    print(f"Completed. Test Accuracy: {test_metrics['accuracy']:.4f}, Test Macro F1: {test_metrics['macro_f1']:.4f}, Test FPR: {test_metrics['false_positive_rate']:.4f}")
    print(f"Evidence saved to: {output}")


if __name__ == "__main__":
    main()
