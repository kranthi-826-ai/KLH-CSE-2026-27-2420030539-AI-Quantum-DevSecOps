# Matched complete-envelope benchmark results

Date: 2026-10-20. Frozen implementation/protocol: `09c59e1`.
The runner completed successfully in236.78 seconds and stopped its owned JVMs.
No application services, models, live data or account permissions changed.

## Measured scope

All modes use the project's actual profile factory and envelope implementation,
the same4096-byte deterministic payload and fixed associated context. Each timed
operation constructs providers, generates fresh recipient and signer key pairs,
seals, opens, checks recovered plaintext equality and wipes the recovered copy.
This follows the Business Service crypto boundary. It excludes AI, policy,
network/authentication, serialization, MySQL and audit delivery.

JMH1.37, average-time mode, one thread, five sequential forks per mode, five
1-second warm-up iterations and ten1-second measurement iterations per fork.
Each mode has50 recorded iteration means. Fixed256–512MiB heap and GC profiler
apply to all modes. CPU:i7-13650HX,20 logical processors; visible RAM16,454,352KiB,
free before run5,676,012KiB; observed CPU load before run9%. JVM21.0.12.1;
Bouncy Castle1.86. CPU affinity, temperature and power state were not controlled.
Automated editing/short checks and other background activity were not excluded;
this is a reproducible development-laptop checkpoint, not an isolated lab run.

## Timing and allocation

| Profile | Mean ms/op | JMH interval ms | Median fork mean ms | Fork mean range ms | Allocated B/op |
|---|---:|---:|---:|---:|---:|
| CLASSICAL |8.057|7.315–8.799|7.450|6.727–10.070|169,486|
| HYBRID |6.685|6.525–6.845|6.657|6.528–7.000|710,814|
| PQC |5.309|5.211–5.406|5.286|5.168–5.442|677,170|

Intervals are JMH's default99.9% score confidence intervals, verified in the
shaded1.37 Result bytecode (`getScoreConfidence` uses0.999). They are not a
guarantee across machines/conditions or independent request-level confidence.
Fork means show substantial variation for CLASSICAL; preserve it instead of
presenting a single precise speed claim. No request p95/p99 was measured.
Allocation estimates describe this JVM workload, not heap peaks or cluster RAM.

PQC was faster in this measured fresh-key path and allocated more bytes than
CLASSICAL. Do not generalize that into “PQC is faster”, an algorithm-security
ranking or an adaptive-system speedup. The profiles implement different security
goals/primitives; equal work boundaries do not imply equal cryptographic strength.
No bottleneck attribution is supported without additional profiling.

## Sampled raw envelope sizes

Separate16 fresh verified round trips per mode sampled lengths, not benchmark
timings. Sizes below exclude metadata, keys, JSON/base64, HTTP/TLS and framing;
they are **not wire sizes**.

| Profile | Encapsulation bytes | Nonce bytes | Ciphertext bytes | Signature bytes observed | Raw component total bytes |
|---|---:|---:|---:|---:|---:|
| CLASSICAL |44|12|4112|70–72|4238–4240|
| HYBRID |1120|12|4112|3309|8553|
| PQC |1088|12|4112|3309|8521|

CLASSICAL uses X25519/AES-256-GCM/ECDSA-P256, HYBRID uses
X-Wing/AES-256-GCM/ML-DSA-65, PQC uses ML-KEM-768/AES-256-GCM/ML-DSA-65.
The44-byte X25519 encapsulation is this implementation's encoded value, not a
claim that the raw X25519 public key is44 bytes. ECDSA signature sizes vary.

## Retained evidence

Ignored directory:
`ml/artifacts/envelope-benchmark-f597f0c412774ed7a9aae8b14d7d7ec1/`.

- `verification.json` SHA256:
  `a042399423c16736c222e3f15d5e64d8525db1cfd48a1e3e5ed5444c8e3150e6`.
- `jmh.json` SHA256:
  `a92f65676a7bc4ecbb6a38014746c4ae9dacd8307e154368124694d8a518d2a1`.
- `sizes.json` SHA256:
  `85db61eef6722c7cca0fee67087d30eca8317b1b6073766b878840666a4bc9d0`.
- `summary.json` SHA256:
  `d7f68a17c50a54c9bffa43278a087276ce1e880937914eca20494919192ce3db`.
- Executed shaded JAR SHA256:
  `ea189309054a14462c4d5667cdd777ff737d4fe09c51cb93907d5971dbba10d2`.

The summary validator checks completed-run receipts and input hashes, distinct
profiles, protocol counts, finite raw samples, recomputed means, allocation
units and size-component consistency. Three validator tests passed; all17
live-verifier/config unit tests passed. Two new Java tests execute actual round
trips in every mode and reject an unknown mode. Raw console/error logs remain
with the artifacts. No secret keys or envelope contents are printed.

Full root `mvn -q test` subsequently exited0:47 freshly written suite reports,
112 tests total,107 passed,five skipped,no failures/errors. Skips remain skips.
`java-regression-fresh.json` SHA256:
`54664f996b565812d05803ced67ccbe56000ed4148975570ca46a72dd2bfa464`.
The earlier optional aggregation `java-regression.json` did not validate report
freshness because PowerShell auto-parsed an ISO timestamp before a redundant
string parse failed. That artifact is retained but not used as acceptance
evidence; the new fail-fast aggregation records the valid UTC threshold and
each report timestamp. This was an aggregation issue, not a Java test failure.
No benchmark or Surefire JVM remained after both runs.

Reproduce using [the frozen protocol](matched-envelope-protocol-v1.md), then
run `scripts/summarize_envelope_benchmark.py` against the new artifact directory.
The analyzer refuses to overwrite a prior summary.

## Remaining publication work

Matched full adaptive-versus-static API experiments with realistic workload
distribution, policy safety/constraint failures, AI/policy/database costs,
request-level tail latency, concurrency, repeated randomized/counterbalanced
orders and controlled host conditions remain unperformed here. More secure
deployment/key management and real service-to-service transport are separate
requirements. These timings do not improve threat-detection accuracy, establish
novelty or guarantee acceptance of a paper.
