# Causal temporal study and explicit frontend guard

Date:2026-10-20. User explicitly removed the previous percentage restriction
and authorized further work. This completes that pending experiment; no new
candidate passes the declared window-level development gates.

## Causal reconstruction and fair comparison

Read continuous raw context beginning70s before each injection in the same16
scenario5 development recordings, both workers (32 traces). No other scenario
or final evaluation data is opened. Construct features on all observed context
windows BEFORE selecting the557 previously labeled observations. Every one of
the original269 feature values and every label is checked for exact agreement.
All selected rows have at least five seconds of real raw warmup. Missing cached
rows are NOT fabricated as zero history; only continuously observed context
supports the absence of observed syscalls. Actual capture loss is not ruled out.

Add32 prior-five-second selected-syscall counts and four event-volume summaries
to the269 features, for305 inputs. Histories exclude the current window and
future windows and reset per container/recording; prediction is after the current
one-second window closes. No attack timestamps, labels, IDs or argument text
enter ML inputs. Raw timestamps regressions larger than1s fail collection
rather than silently supporting an unsafe forward cutoff.

Preserve the exact original557-row order for fixed-seed model fitting. Reordering
training rows alone can alter tree bootstraps and confound an ablation. Base
and rich pipeline metrics reproduce the previous study exactly. Same three
fixed recipes, eight leave-one-CVE-out folds holding both recordings together,
threshold0.5,95% exposure-recall and5% control-alarm gates.

| Temporal model | Exposure hits/51 | Control alarms/506 | Macro-F1 |
|---|---:|---:|---:|
| Logistic |39 (76.47%) |20 (3.953%) |0.83861 |
| RF |36 (70.59%) |0 observed |0.90649 |
| XGBoost |36 (70.59%) |1 (0.198%) |0.90129 |

The best earlier ML recall remains40/51 (78.43%) with3/506 alarms, from base
logistic. Temporal history as defined here did not solve the difficult cases.
No winner model is fitted for independent evaluation. Zero observed alarms
does not prove zero false-positive risk.

## Separate exploratory guard, not an ML accuracy improvement

After the temporal negative result, declared an explicit hypothesis for the
selected frontend target pods: alert on observed current or prior-five-second
execve/execveat, independently of the statistical classifier. Its plan was
saved before guard scoring. This is posthoc development engineering, not a
new independently validated ML model or general rule that process execution
is malicious. Legitimate frontend process execution must be evaluated on
broader normal data. No runtime trust/role enforcement is implemented here.

Using unchanged grouped out-of-fold base-logistic predictions:

| Decision | Exposure hits/51 | Control alarms/506 |
|---|---:|---:|
| ML alone |40 |3 |
| Explicit execution guard alone |41 |0 observed |
| ML OR explicit execution guard |41 (80.39%) |3 (0.593%) |

The combination adds only one window and still misses10/51. It is not95% or
99% detection, not pure-ML improvement, and not accepted for deployment.
Exposure intervals do not certify malicious behaviour in every second or
successful exploitation. More tuning against the same small development set
would not establish reliability. The next priority is targeted annotation and
observability review before another model search; never relabel missed rows
simply to improve a number.

## Reproduction and evidence

Data scripts: `socialnetwork_temporal.py`, `prepare_socialnetwork_temporal.py`.
Studies: `study_socialnetwork_temporal.py` and
`study_frontend_execution_guard.py`, all under `ml/`. Local ignored datasets
and candidates use the `socialnetwork-temporal-*` and
`socialnetwork-execution-guard-v1` directories. Plans, full grouped results,
predictions, coverage and hashes retained; output directories are exclusive.

Tests cover future-prefix invariance, exclusion of current-window history,
container/recording isolation, warmup, verified sparse gaps, canonical order
and explicit guard inputs. Full ML suite100 passed. Promoted UNSW checksum
unchanged. No enforcement, service configuration or unrelated UI changes.
