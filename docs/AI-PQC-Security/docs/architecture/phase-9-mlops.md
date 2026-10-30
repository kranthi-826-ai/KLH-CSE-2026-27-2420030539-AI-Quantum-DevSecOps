# Phase 9 Local-First MLOps

The MLOps lifecycle is deliberately free and local: official UNSW-NB15 files,
reproducible preprocessing, MLflow SQLite tracking, immutable dataset/model
hashes, fail-closed promotion, runtime drift reports, and manual rollback.

## Promotion contract

The validation split chooses the candidate. The official test split is used
once for final evidence. Promotion requires at least 0.89 macro F1, 0.95 attack
recall, 0.98 ROC-AUC, and no more than 0.20 false-positive rate. These gates
match the verified baseline boundary; future candidates must tighten them only
after a reproducible experiment, never by selecting on the test set.

The promoter verifies the model hash after copying and writes metadata beside
the promoted binary. Both remain local because model binaries, MLflow state,
raw data, and generated reports are Git-ignored. A deployment selects the model
through `AI_MODEL_PATH`, so rollback is a path change rather than a code change.

## Drift policy

Numeric features use population stability index and categorical features use
total-variation distance. A score of 0.20 or greater is flagged. Drift does not
prove an attack and does not trigger automatic retraining; it opens an
evaluation step using a versioned observation window. Generated microservice
events remain a separate system dataset and are never silently mixed into the
UNSW-NB15 benchmark.
