# Dependency response contract checks

Date: 2026-10-20. These checks concern fail-closed application behavior, not
intrusion-detection accuracy or a new model promotion.

## Required boundaries

Policy-to-AI responses must contain an explicit classifier label and finite
score in [0,1], a risk band consistent with the reviewed .35/.70 boundaries,
the echoed request correlation, a 16-character lowercase model hash prefix,
a bounded model name and nonblank bounded explanation. Missing numeric or
boolean fields must remain missing, never default to zero/false. The model's
classifier label is not inferred from the risk-band boundaries.

Business-to-Policy responses must contain a finite score, consistent input and
sensitivity-adjusted effective risk, an allowed mode/profile pair compatible
with the request, the expected correlation, bounded decision identity and
provenance for reviewed policy 1.1.0. Invalid decisions must leave a FAILED,
unverified execution with no selected decision/mode or cryptographic latency.
The pre-existing HIGH plus CLASSICAL denial remains in force.

## Verification scope

Actual loopback HTTP fixtures exercise AI JSON decoding, missing fields,
invalid score ranges, contradictory risk, invalid metadata, malformed bodies,
and six valid boundary scores. Business checks include actual HTTP decoding
of omitted/null policy scores and mocked contradictory/incompatible decisions.
Fixtures are synthetic dependency responses, not real attacks or substitutes
for the healthy model. Full root packaging and the existing real-model local
API/MySQL matrix must be rerun against the resulting application binaries.

## Limits

These checks establish consistency with a reviewed contract, not authenticity
or model attestation. A compromised dependency can fabricate consistent fields.
Hash-prefix syntax is not an allowlist or independent artifact verification.
Policy version changes require explicit review of both boundaries. The Business
Service does not implement a second copy of every policy-selection preference.
Inputs remain demonstration features/sensitivity, not trusted network telemetry.
Body-size/whole-request deadlines, slow-drip responses, concurrent load and
production transport hardening remain separate requirements.
