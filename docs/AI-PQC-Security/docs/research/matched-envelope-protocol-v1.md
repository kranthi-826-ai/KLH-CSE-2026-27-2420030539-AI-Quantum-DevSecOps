# Matched complete-envelope performance protocol

Freeze before execution. This extends the short primitive timings with a
matched workload, not a claim of adaptive-system speedup or stronger security.

- Actual `CryptoProfileFactory` and `SecureEnvelopeService` implementations.
- CLASSICAL, HYBRID and PQC profiles, identical 4096-byte deterministic payload
  and fixed associated context. No real application data or secrets.
- Every measured operation creates its provider and both recipient/signing key
  pairs, seals, opens, verifies plaintext equality and wipes the recovered copy.
  This matches the Business Service cryptographic boundary, not its full API.
- JMH average-time milliseconds/operation; one thread; five sequential forks;
  five 1-second warm-up and ten 1-second measurement iterations per fork.
  Fixed256–512MiB heap; GC profiler applied to all profiles; fail on errors.
- Three profile results with50 measured iteration means per profile. Report JMH
  mean/interval and fork means, not a request p95 from aggregated iteration data.
  GC allocation estimates are not full process/cluster resource measurements.
- Separate16 fresh verified size samples per profile. Report raw encapsulation,
  nonce, ciphertext and signature lengths; ECDSA signatures may vary. Totals
  exclude JSON/base64, metadata, transport framing and keys: not wire sizes.
- Unique artifact directory; never overwrite earlier runs. Retain JSON, logs,
  JAR hash, source revision, protocol, CPU/RAM context and timings. Stop only
  owned benchmark JVMs; hard600-second experiment deadline.

Build the benchmark reactor, then run `scripts/run-envelope-benchmarks.ps1`.
Results are ignored under `ml/artifacts/envelope-benchmark-<run-id>/`.
Do not use the earlier overwrite-prone primitive-run helper for this protocol.

Limitations: laptop power/thermal state and background load are not externally
controlled; CPU affinity and randomized profile order are not provided. One
multi-fork run is not a cross-machine replication. No AI inference, policy
service, audit delivery, MySQL, network/TLS, user concurrency or API-tail-latency
cost is inside this boundary. Adaptive versus static system comparison remains
separate. No model accuracy claim can be inferred from these timings.
