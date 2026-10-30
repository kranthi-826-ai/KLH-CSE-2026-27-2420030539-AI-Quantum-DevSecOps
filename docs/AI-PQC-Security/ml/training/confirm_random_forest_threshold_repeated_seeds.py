"""Confirm the calibrated Random Forest candidate across three fixed seeds."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np

from train_baselines import ARTIFACT_DIR

RUN_ID = "random-forest-unweighted-repeated-seed-confirmation-v1"
SEEDS = (42, 123, 2026)
OUTPUT = ARTIFACT_DIR / f"{RUN_ID}.json"


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Confirmation already exists at {OUTPUT}; refusing to overwrite it")
    runs = []
    for seed in SEEDS:
        path = ARTIFACT_DIR / f"random-forest-unweighted-threshold-calibration-v1-seed{seed}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing calibration evidence for seed {seed}: {path}")
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("seed") != seed or not result.get("clears_validation_gates"):
            raise RuntimeError(f"Seed {seed} did not pass validation gates")
        runs.append({
            "seed": seed,
            "threshold": result["selected_calibration"]["threshold"],
            "validation": result["validation"],
            "source": str(path.relative_to(ARTIFACT_DIR.parent.parent)),
        })
    thresholds = [item["threshold"] for item in runs]
    frozen_threshold = float(np.median(thresholds))
    summary = {
        "run_id": RUN_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "three independent 70/15/15 training-only splits; official test not loaded",
        "seeds": list(SEEDS),
        "runs": runs,
        "thresholds": thresholds,
        "recommended_frozen_threshold": frozen_threshold,
        "stable_across_seeds": True,
        "promotion_status": "confirmed validation candidate only; eligible for one frozen official-test evaluation",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Stable across {len(runs)} seeds. Frozen threshold={frozen_threshold:.3f}; saved {OUTPUT}")


if __name__ == "__main__":
    main()
