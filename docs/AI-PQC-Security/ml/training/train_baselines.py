"""Train leakage-safe binary UNSW-NB15 baselines and record evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import pandas as pd
import sklearn
import mlflow
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ML_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ML_ROOT / "data" / "raw" / "unsw-nb15"
ARTIFACT_DIR = ML_ROOT / "artifacts"
MODEL_DIR = ML_ROOT / "models"
SEED = 42
CATEGORICAL = ["proto", "service", "state"]
EXCLUDED = ["id", "attack_cat", "label"]
FILES = {
    "training": (DATA_DIR / "UNSW_NB15_training-set.csv", 175_341),
    "testing": (DATA_DIR / "UNSW_NB15_testing-set.csv", 82_332),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    train = pd.read_csv(FILES["training"][0])
    test = pd.read_csv(FILES["testing"][0])
    if len(train) != FILES["training"][1] or len(test) != FILES["testing"][1]:
        raise ValueError("Unexpected row count; run validate_unsw_nb15.py first")
    if list(train.columns) != list(test.columns):
        raise ValueError("Training and testing schemas differ; run validation first")
    features = [column for column in train.columns if column not in EXCLUDED]
    return train[features], train["label"].astype(int), test[features], test["label"].astype(int)


def preprocessor(columns: list[str]) -> ColumnTransformer:
    categorical = [column for column in CATEGORICAL if column in columns]
    numeric = [column for column in columns if column not in categorical]
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )


def models(columns: list[str]) -> dict[str, Pipeline]:
    return {
        "logistic": Pipeline(
            [
                ("preprocess", preprocessor(columns)),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1_000, class_weight="balanced", random_state=SEED
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", preprocessor(columns)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        max_depth=24,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=SEED,
                    ),
                ),
            ]
        ),
        "rf_unweighted": Pipeline(
            [
                ("preprocess", preprocessor(columns)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=24,
                        min_samples_leaf=2,
                        class_weight=None,
                        n_jobs=-1,
                        random_state=SEED,
                    ),
                ),
            ]
        ),
    }


def metrics(model: Pipeline, features: pd.DataFrame, labels: pd.Series) -> dict:
    started = time.perf_counter()
    predictions = model.predict(features)
    elapsed = time.perf_counter() - started
    probabilities = model.predict_proba(features)[:, 1]
    macro = precision_recall_fscore_support(labels, predictions, average="macro", zero_division=0)
    weighted = precision_recall_fscore_support(labels, predictions, average="weighted", zero_division=0)
    attack = precision_recall_fscore_support(labels, predictions, labels=[1], average=None, zero_division=0)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "accuracy": accuracy_score(labels, predictions),
        "macro_precision": macro[0], "macro_recall": macro[1], "macro_f1": macro[2],
        "weighted_precision": weighted[0], "weighted_recall": weighted[1], "weighted_f1": weighted[2],
        "attack_precision": attack[0][0], "attack_recall": attack[1][0], "attack_f1": attack[2][0],
        "roc_auc": roc_auc_score(labels, probabilities),
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "inference_total_seconds": elapsed,
        "inference_ms_per_sample": elapsed * 1000 / len(features),
        "confusion_matrix": [[int(value) for value in row] for row in matrix],
        "samples": len(features), "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def json_safe(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["logistic", "random_forest", "rf_unweighted", "all"], default="all")
    args = parser.parse_args()
    x_official_train, y_official_train, x_test, y_test = load_data()
    x_train, x_validation, y_train, y_validation = train_test_split(
        x_official_train,
        y_official_train,
        test_size=0.20,
        stratify=y_official_train,
        random_state=SEED,
    )
    selected = models(list(x_train.columns))
    if args.model != "all":
        selected = {args.model: selected[args.model]}
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "task": "UNSW-NB15 binary intrusion classification",
        "seed": SEED,
        "selection_metric": "validation_macro_f1",
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "mlflow": mlflow.__version__,
        },
        "dataset_sha256": {
            name: sha256(path) for name, (path, _) in FILES.items()
        },
        "split": {"train": len(x_train), "validation": len(x_validation), "test": len(x_test)},
        "models": {},
    }
    for name, pipeline in selected.items():
        started = time.perf_counter()
        pipeline.fit(x_train, y_train)
        train_seconds = time.perf_counter() - started
        result = {
            "training_seconds": train_seconds,
            "validation": metrics(pipeline, x_validation, y_validation),
            "test": metrics(pipeline, x_test, y_test),
        }
        summary["models"][name] = result
        joblib.dump(pipeline, MODEL_DIR / f"{name}.joblib")
        database_path = (ML_ROOT / "mlflow.db").as_posix()
        mlflow.set_tracking_uri(f"sqlite:///{database_path}")
        mlflow.set_experiment("ai-pqc-unsw-nb15")
        with mlflow.start_run(run_name=name):
            mlflow.log_params({"model": name, "seed": SEED, "task": "binary"})
            mlflow.log_metrics({f"validation_{k}": v for k, v in result["validation"].items() if isinstance(v, (int, float))})
            mlflow.log_metrics({f"test_{k}": v for k, v in result["test"].items() if isinstance(v, (int, float))})
    winner = max(summary["models"], key=lambda name: summary["models"][name]["validation"]["macro_f1"])
    summary["validation_winner"] = winner
    output_name = "baseline-results.json" if args.model == "all" else f"baseline-results-{args.model}.json"
    output = ARTIFACT_DIR / output_name
    output.write_text(json.dumps(summary, indent=2, default=json_safe), encoding="utf-8")
    print(f"Completed. Validation winner: {winner}. Evidence: {output}")


if __name__ == "__main__":
    main()
