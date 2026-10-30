# Rich-context HTTP detector: large measured improvement, no release

Date: 2026-10-19. A new peer-holdout dataset and one frozen test. This addresses
the requested large improvement; it does not claim perfect AI or production
readiness. Existing promoted models and automatic response settings are unchanged.

## Hypothesis and representation

The earlier peer-only model mixed failures from unrelated credential contexts.
The new representation retains all nine original peer/route/header features
and adds 15 context/route/history features: previous successes/failures,
consecutive failures, previous outcome indicators, context novelty, bearer-context
churn and elapsed context time. Only already completed earlier responses are
used. The current response, scenario, target, identity and token authenticity
are not inputs. There is no new JWT-validation result handed to the classifier.

Credential-context matching uses a random per-process HMAC-SHA256 key over the
authorization value, scoped to route and actual connection peer. Raw tokens,
context digests/keys and account identifiers are not exported. These keys are
bounded in-memory state, lazily pruned with the history/idle-peer rules; this
does not promise exact wall-clock memory erasure. Aggregate peer counters are
retained so changing credentials does not erase all failure/churn evidence.
Context matching is not authenticated identity or an evasion-proof mechanism.

Feature version `v2` is explicitly opt-in. Default capture remains disabled,
with `v1` the default schema. Unsupported versions refuse startup; runtime
feature failures drop telemetry rather than reject a request. The existing
queue, memory, expiry and output-size bounds still apply.

## Fresh and harder collection

The real Gateway-to-Auth/H2 lab made **1,478 HTTP requests** in **88.11 seconds**:
160 setup operations plus **1,318 study observations** from **80 accounts/
sessions**. Seed 20261021 is an arbitrary reproducibility seed, not a collection
date. Three/two/two actual loopback transport peers are disjoint across phases.

| Partition | Sessions | Rows | Actual transport peers |
|---|---:|---:|---:|
| Train | 48 | 774 | 3 |
| Calibration | 16 | 268 | 2 |
| Final test | 16 | 276 | 2 |

The original six scenarios were preserved and two were added: legitimate token
refresh as a negative control and rotating invalid tokens as a positive-intent
case. Repeated/rotating invalid tokens now corrupt the signature of an actual
JWT, preserving its length, encoding shape and claims rather than using a fixed
short marker. The model never sees token bytes or token length. Labels remain
harness intent; legitimate mistakes remain negative even when an individual
request correctly receives 401. All labels were joined to server-generated
observation IDs and actual gateway pre-request feature snapshots.

## Predeclared training and fair comparison

For **each** feature set (rich 24 features and original nine features), the same
three candidates were compared using leave-one-training-peer-out CV and mean
partial ROC-AUC at maximum FPR .05: standardized logistic regression, bounded
Random Forest, and bounded XGBoost. Calibration was separate. Plans, code/data/
model hashes and thresholds were frozen before the fresh final test.

The selected rich model was RF (240 trees, depth 8, minimum leaf 2, balanced
weights, four threads). Calibration recall was 96.30%, FPR 0%, accuracy 98.13%.
The matched nine-feature pipeline selected logistic regression and failed
calibration gates. The older frozen peer-trained logistic was also retained as
a fixed reference. No final-test result was used to retune any candidate.

The predeclared large-gain target was at least +10 percentage points accuracy
and +20 points recall against the old peer reference on the **same fresh test**,
with rich FPR <=5%. Strict quality gates independently require calibration and
final recall >=95% with FPR <=5%; satisfying the large-gain goal is not a release.

## One-time final results: identical 276 test requests

| Pipeline | Accuracy | Macro-F1 | Suspicious-intent recall | Observed FPR |
|---|---:|---:|---:|---:|
| Older frozen peer model | 60.51% | 54.12% | 23.70% | 4.26% |
| Matched nine-feature search | 61.23% | 57.38% | 31.85% | 10.64% |
| Rich-context search | **97.10%** | **97.09%** | **94.07%** | **0/141** |

Against the matched feature-search pipeline, accuracy improved **35.87 percentage
points**, recall **62.22 points** and macro-F1 **39.72 points**. Against the old
frozen peer reference, gains were 36.59 accuracy and 70.37 recall points.
These are paired results on this fresh test, not a subtraction across different
datasets. The rich and base searches selected different algorithms, so the
comparison is between feature/model-selection pipelines, not a causal isolation
of features with the estimator held fixed.

The rich confusion matrix is `[[141,0],[8,127]]`. It missed eight of 135
suspicious-intent requests; each of the four positive scenario types had two
misses. Recall by type: credential guessing 93.55%, repeated invalid tokens
95.00%, missing tokens 93.94%, rotating invalid tokens 93.55%. No benign test
request, including legitimate bursts, mistakes and refresh, raised an alert.
Zero observed FPs on a small sample does not prove zero population FPR.

**Large-improvement target: passed. Strict final recall gate: failed.** The
model remains a non-enforcing experimental candidate; no automatic blocking,
policy substitution or production promotion occurred. This does not change
the separate CICIoT/UNSW accuracy figures or prove superiority to published work.

## Limits, verification and reproduction

Only one host/generator/run and two final test peers were used. Peer bootstrap
intervals are descriptive and especially fragile with two groups; near-equal
results between these peers do not establish narrow population uncertainty.
Cold/rotating credentials, shared clients, adversarial pacing, unknown attack
families and production traffic still require independent evaluation. The
observed misses are consistent with limited information on initial probes, but
request-position causes were not established and no first-request guarantee is
made. Cryptographic authentication and rate limits remain separate controls.

- Evidence packet: `docs/research/evidence/rich-context-http-v1.json` includes
  the manifest, both feature searches, frozen parameters, final paired metrics,
  scenario results, model/source hashes and gate decisions.
- `scripts/run-rich-http-study.ps1` reproduces component steps into fresh paths.
  Its syntax was checked; collection/preparation/training/evaluation components
  were executed individually for this recorded run. No repeat test was used.
- `ml/training/study_rich_http.py` refuses overwrites and repeated test attempts;
  it verifies frozen dependencies and model checksums before opening final data.
- Python suite: **65 passed**. Full Java reactor: **60 passed**, five opt-in
  collection tests skipped normally; real routed rich collection passed explicitly.
- Java tests cover context isolation, causal snapshots, preserved aggregate
  evidence under token rotation, per-instance key separation and no exported
  token/digest. Python tests cover the 24-feature contract, nonconstant same-format
  corruption, bounded model search and one-shot evaluation refusal.
- No system/security settings were disabled, no MySQL password was needed,
  no external hosts were targeted and no existing model binary was overwritten.

Final completion audit verified the evidence/local JSON equality, all model,
dataset and training-script hashes, derived confusion-matrix metrics, 1,318
secret-free numeric feature records, seven disjoint peers and all eight
scenarios. It confirmed the predeclared large-gain target passed while the
strict recall gate correctly failed. No inference was repeated in that audit.
The weekly meter reported 28% used/72% remaining, preserving the earlier
70%-remaining reserve; it is an account-wide coarse reading, not an exact cost.
