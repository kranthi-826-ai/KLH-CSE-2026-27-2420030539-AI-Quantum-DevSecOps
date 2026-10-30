# Pre-injection control addendum

Declared 2026-10-20 while exposure scoring is running, before inspecting any
exposure scores or summary outcomes. This addendum changes neither the trained
reference model nor its June-normal calibration threshold. It adds controls,
not tuning or a new candidate.

For each of the same eight scenario5/plain_workload/collection1 CVE cases,
process both worker traces and select the affected pod's full one-second
windows between 60 and 10 seconds before the annotated attack start. Use the
same 29 features, omit slice boundary windows, and preserve missing coverage.
The annotation must say CMDs: 0 and its Attack interval must agree with
dates.txt. Call these pre-injection controls, not proof of a clean host.
No control window may overlap the attack interval. Do not treat other pods or
all other trace timestamps as ground-truth normal automatically.

Report control alarms per case and overall alongside exposure alerts. Do not
advertise exposure alerts as useful discrimination if matched pre-injection
controls are also anomalous. The earlier June normal check alone cannot rule
out June-to-November domain shift. No parameter/threshold change is allowed
using these results, and scenarios1/3/7 and collection2 remain unscored.
