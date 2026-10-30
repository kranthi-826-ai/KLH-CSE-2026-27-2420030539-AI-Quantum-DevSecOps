# CICIoT2023 family-aware refinement, v1

Date: 2026-10-19. Outcome: no eligible candidate; no model promoted.

The first pilot identified brute force, reconnaissance and web attacks as weak
families. Four predefined XGBoost recipes tested training weights for those
families and for benign traffic. The search plan, parameters, seed and script
hash were saved before fitting.

All selection data came from the frozen 230,242-row training partition, internally
split 70/15/15 and stratified by subtype. The outer calibration, validation and
reserved test files were not opened because none of the initial candidates met
both recall >=95% and false-positive rate <=5%. Planned repeated-seed confirmation
was therefore not triggered; these are single-seed internal results.

| Recipe | Accuracy | Macro-F1 | Attack recall | Weak-family recall | FPR |
|---|---:|---:|---:|---:|---:|
| Reference | 89.19% | 87.18% | 87.08% | 56.57% | 4.79% |
| Family weighted | 89.36% | 87.35% | 87.35% | 57.88% | 4.93% |
| Benign weighted | 89.49% | 87.49% | 87.56% | 58.59% | 5.01% |
| Family weighted, deeper | 89.84% | 87.87% | 87.96% | 60.04% | 4.83% |

Weak-family recall pools attack examples from BruteForce, Recon and Web-based.
It is binary detection recall, not attack-family classification accuracy. The
deeper candidate improved it by about 3.47 percentage points under this internal
protocol. The result does not update the outer pilot's 90.90% XGBoost accuracy,
is not a cross-dataset improvement, and does not support deployment.

Calibration selects macro-F1 within the 5% FPR ceiling. Where no threshold also
meets the recall floor, a diagnostic fallback threshold is reported and marked
ineligible. The benign-weighted candidate slightly exceeded the FPR ceiling on
internal validation, illustrating why calibration alone cannot prove eligibility.

Evidence:

- `ml/training/refine_ciciot2023.py`
- `ml/artifacts/ciciot2023-family-refinement-v1-plan.json`
- `ml/artifacts/ciciot2023-family-refinement-v1.json`

Next hypothesis: additional representative benign/weak-family data and richer
application/runtime signals may matter more than further weighting this capped
feature sample. Any new experiment must have a bounded plan and preserve the
reserved test. Live microservice transfer still requires compatible measured
features; it cannot be inferred from these offline results.
