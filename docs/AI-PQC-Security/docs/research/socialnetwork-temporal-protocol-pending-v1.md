# Pending causal temporal experiment — NOT EXECUTED

Update2026-10-20: the user explicitly removed the percentage restriction and
asked to proceed. This experiment is now complete; see
`socialnetwork-temporal-study-v1.md` for negative results and guard limitations.
The checkpoint below records the earlier stop, not the current state.
The original matched row order must also be preserved for fixed-seed comparisons.

Checkpoint:2026-10-20. Latest account usage tool reading is6% used; the first
reading after the weekly reset was0%. User requested no more than seven weekly
percentage points for this work. Readings are coarse and account-wide. Do not
start another model-search batch without renewed budget approval; do not use a
reset credit or weaken the experiment just to squeeze it into remaining quota.
No temporal candidate, dataset or accuracy result exists at this checkpoint.

## Hypothesis and required data

Nine of11 misses in the expanded base-logistic development study belong to
CVE-2022-0492. Recent syscall behaviour may carry information absent from an
independent one-second snapshot. This remains a hypothesis, not a proven cause.

Reconstruct continuously observed raw context for both development collections
in scenario5. Include at least70 seconds before injection plus the original
post-interval boundary cushion. Compute features for all observed windows
BEFORE selecting annotation-labeled windows. Preserve/recheck all557 current
feature/label rows; other scenarios remain independent and unscored.

Do NOT compute temporal history from only the filtered557-row cache: it omits
the ten seconds before injection and other unlabeled windows. Treating those
missing rows as zero activity would create an annotation-induced artifact.
Zero activity is valid only when continuous raw coverage actually establishes
that the relevant container had no observed events during a past interval.

## Fixed feature proposal and safeguards

Keep the current269 features. Add prior-five-second selected syscall counts
and simple event-volume summaries. Each prediction occurs after its current
one-second window closes. Historical inputs must come strictly from earlier
completed windows, with state isolated per container AND recording. No future
events, injection timestamps, case/label indicators, replica IDs or argument
text may enter model features. Emit observed-history coverage explicitly and
require sufficient raw warmup rather than inventing history.

Unit-test prefix invariance (future events cannot change earlier features),
container/recording isolation, real zero-activity gaps and warmup handling.
Match original windows/features/labels before scoring. Run the same three
fixed recipes, threshold0.5, and leave one CVE out across BOTH recordings in
each fold. Keep95% exposure-recall and5% control-alarm gates; no threshold
search or final-test access. Freeze a candidate only if gates pass, then
design an independent evaluation. Never claim99% or production readiness
from these small, correlated development observations.
