# Phase 5 Cryptographic Benchmark Results

Experiment date: 2026-09-30

This experiment measures the executable algorithms used by the project's
crypto-agility layer. It provides a reproducible performance baseline for
adaptive policy work; it does not certify cryptographic security or prove that
the same timings will occur on another computer.

## Results

JMH reports average time per operation. Lower is faster.

| Operation | Mean | Observed range | Purpose |
|---|---:|---:|---|
| AES-256-GCM encrypt, 4 KiB | 3.043 us | 3.015-3.083 us | Classical authenticated payload encryption |
| ML-KEM-768 encapsulation | 34.539 us | 33.028-35.835 us | NIST post-quantum key establishment |
| Hybrid X-Wing encapsulation | 105.702 us | 104.564-106.759 us | Combined classical and PQC key establishment |
| X25519 encapsulation | 210.821 us | 206.314-214.947 us | Classical key-establishment comparison |
| ML-DSA-65 sign, 4 KiB | 692.220 us | 669.714-717.642 us | NIST post-quantum digital signature |

The result demonstrates that all five real cryptographic paths execute on the
target development laptop. It must not be interpreted as a direct ranking of
algorithm security. The X25519 and hybrid implementations also perform
different setup and composition work, so their timings are not an
apples-to-apples primitive-only comparison.

## Protocol

- Harness: JMH 1.37, average-time mode, one thread
- Warm-up: 2 iterations of 1 second
- Measurement: 3 iterations of 1 second
- Forks: 1
- JVM: Eclipse Adoptium OpenJDK 21.0.12.1, 64-bit HotSpot
- CPU: 13th Gen Intel Core i7-13650HX
- Memory: 16 GB installed
- Cryptographic provider: Bouncy Castle through the project's Java 21 modules

The short protocol is suitable for a development checkpoint. A publication
claim requires longer warm-up and measurement periods, multiple forks, repeated
runs under controlled power and thermal conditions, and statistical comparison
against explicitly matched baselines.

## Reproduction

Build the Maven reactor, then run from the repository root:

```powershell
.\scripts\run-crypto-benchmarks.ps1
```

The raw JSON is written to `ml/artifacts/crypto-benchmark.json`. The artifacts
directory is intentionally Git-ignored because raw runs are regenerated for
each controlled experiment.

## Next research experiment

Repeat each benchmark with at least 5 forks and 10 measurement iterations,
capture system load and temperature conditions, and report median, confidence
interval, throughput, ciphertext/signature sizes, and end-to-end API latency.
That expanded experiment will support the paper's security-versus-performance
analysis of classical, hybrid, and post-quantum policy choices.
