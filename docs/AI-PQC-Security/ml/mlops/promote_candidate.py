"""Promote a verified model only when reproducible quality gates pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_GATES = {
    "macro_f1": 0.89,
    "attack_recall": 0.95,
    "false_positive_rate_max": 0.20,
    "roc_auc": 0.98,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gate_failures(metrics: dict, gates: dict = DEFAULT_GATES) -> list[str]:
    checks = {
        "macro_f1": metrics["macro_f1"] >= gates["macro_f1"],
        "attack_recall": metrics["attack_recall"] >= gates["attack_recall"],
        "false_positive_rate": metrics["false_positive_rate"]
        <= gates["false_positive_rate_max"],
        "roc_auc": metrics["roc_auc"] >= gates["roc_auc"],
    }
    return [name for name, passed in checks.items() if not passed]


def promote(results_path: Path, model_path: Path, output_dir: Path) -> dict:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    winner = results["validation_winner"]
    if model_path.stem != winner:
        raise ValueError(
            f"Candidate {model_path.stem!r} is not validation winner {winner!r}"
        )
    metrics = results["models"][winner]["test"]
    failures = gate_failures(metrics)
    if failures:
        raise ValueError(f"Promotion gates failed: {', '.join(failures)}")
    if not model_path.is_file():
        raise FileNotFoundError(model_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_hash = sha256(model_path)
    metadata = {
        "model_name": winner,
        "model_sha256": candidate_hash,
        "dataset_sha256": results["dataset_sha256"],
        "selection_metric": results["selection_metric"],
        "quality_gates": DEFAULT_GATES,
        "test_metrics": {key: metrics[key] for key in DEFAULT_GATES if key in metrics},
        "false_positive_rate": metrics["false_positive_rate"],
        "promoted_at": datetime.now(timezone.utc).isoformat(),
    }
    with tempfile.TemporaryDirectory(dir=output_dir) as temporary:
        temporary_dir = Path(temporary)
        temporary_model = temporary_dir / "model.joblib"
        temporary_metadata = temporary_dir / "metadata.json"
        shutil.copy2(model_path, temporary_model)
        temporary_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        if sha256(temporary_model) != candidate_hash:
            raise RuntimeError("Model hash changed during promotion")
        temporary_model.replace(output_dir / "model.joblib")
        temporary_metadata.replace(output_dir / "metadata.json")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("ml/artifacts/baseline-results.json"))
    parser.add_argument("--model", type=Path, default=Path("ml/models/random_forest.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("ml/models/promoted"))
    args = parser.parse_args()
    metadata = promote(args.results, args.model, args.output_dir)
    print(f"Promoted {metadata['model_name']} ({metadata['model_sha256'][:16]}).")


if __name__ == "__main__":
    main()
