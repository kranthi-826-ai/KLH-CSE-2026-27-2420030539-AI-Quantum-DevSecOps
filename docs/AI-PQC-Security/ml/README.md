# Phase 3 ML Pipeline

This directory contains the reproducible research pipeline for UNSW-NB15.
Raw data, generated reports, MLflow state, and trained binaries are local
artifacts and are excluded from Git.

## 1. Create the local environment

From the repository root in PowerShell:

```powershell
py -m venv ml/.venv
ml/.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ml/requirements.txt
```

## 2. Obtain the official data

Follow `ml/data/README.md`. Put the two official files in `ml/data/raw/unsw-nb15/`.

## 3. Validate provenance and schema

```powershell
python ml/data/validate_unsw_nb15.py
```

The validator writes `ml/artifacts/dataset-validation.json`, including file
hashes, row counts, schema, missing values, duplicate counts, and label counts.

## 4. Train and evaluate

```powershell
python ml/training/train_baselines.py --model all
```

The script selects using validation macro F1, then evaluates each fitted model
on the official held-out test file. Results and confusion matrices are written
under `ml/artifacts/`. The same evidence is recorded by MLflow in the local
SQLite database `ml/mlflow.db`.

The first run can take several minutes. Use `--model logistic` for the lightest
sanity check.

## 4a. Validation-only candidate search

For iterative model selection, use the validation-only runner instead of
re-running the baseline command above:

```powershell
python ml/training/validation_sweep.py
```

This runner reads only the official training CSV, creates the fixed stratified
80/20 train/validation split, and writes `ml/artifacts/validation-sweep-20261001.json`.
It does not load or score the official test CSV, overwrite baseline model files,
or promote a candidate. After candidate selection and review, run the frozen
recipe's final evaluation once as a separately recorded study step.

For the next bounded XGBoost comparison, run:

```powershell
python ml/training/validation_xgboost_sweep.py
```

It compares four CPU-feasible configurations using two worker threads, applies
predeclared macro-F1, attack-recall and false-positive-rate gates, and saves only
an eligible validation candidate under `ml/models/candidates/`. It never loads
the official test CSV. A higher validation accuracy alone does not qualify a
model or authorize final-test evaluation.

After selecting a model family, calibrate its decision threshold with a new
three-way split:

```powershell
python ml/training/calibrate_xgboost_threshold.py
```

This experiment uses 70% of the official training file for fitting, 15% for
threshold selection, and an untouched 15% for validation. It trains the Random
Forest reference on the same fit rows so comparisons use identical data. The
threshold must keep FPR at or below 6.04%, preserve at least 95.46% attack
recall, and beat the reference validation macro-F1. The official test CSV is
not opened.

## 5. Promote through quality gates

Promotion is fail-closed: the validation winner must meet held-out macro-F1,
attack-recall, false-positive-rate, and ROC-AUC gates. The binary and its hash,
dataset hashes, metrics, and timestamp are copied atomically to a Git-ignored
local registry.

```powershell
python ml/mlops/promote_candidate.py
```

Point `AI_MODEL_PATH` to `./ml/models/promoted/model.joblib` only after this
command succeeds. Keep the original candidate for rollback.

## 6. Detect drift

Export runtime network-flow features to a separate CSV; do not merge security
events into UNSW-NB15. Compare that observation window with the official
training reference:

```powershell
python ml/evaluation/detect_drift.py --reference <reference.csv> --current <runtime-window.csv>
```

Drift creates evidence for investigation or retraining. It never automatically
promotes a new model.
