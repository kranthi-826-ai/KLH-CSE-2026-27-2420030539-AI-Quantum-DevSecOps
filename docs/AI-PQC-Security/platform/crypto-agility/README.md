# Cryptographic Agility Layer

This Phase 5 library executes the profiles selected by the adaptive policy
engine using maintained cryptographic implementations:

- Classical: X25519 key agreement, AES-256-GCM, and ECDSA P-256.
- Hybrid: Bouncy Castle X-Wing, combining X25519 and ML-KEM-768.
- Post-quantum: NIST ML-KEM-768 and ML-DSA-65 through Bouncy Castle 1.86.
- Secure envelope: KEM-derived AES key, authenticated encryption, detached
  signature, algorithm metadata, and associated policy/correlation data.

The implementation does not invent cryptographic primitives. It uses Java 21
JCA/JCE and Bouncy Castle, with domain-separated HKDF composition.

## Test

```powershell
backend/business-service/mvnw.cmd -f platform/crypto-agility/pom.xml test
```

## Benchmark

Build and run JMH on an otherwise idle machine:

```powershell
backend/business-service/mvnw.cmd -f platform/crypto-agility/pom.xml package
java -jar platform/crypto-agility/benchmarks/target/crypto-benchmarks.jar -rf json -rff ml/artifacts/crypto-jmh.json
```

Record the CPU, JVM, OS, provider version, payload size, warmups, forks, and raw
JSON with every reported result. Microbenchmarks measure primitive operations;
they are not a claim of end-to-end application latency or certification.
