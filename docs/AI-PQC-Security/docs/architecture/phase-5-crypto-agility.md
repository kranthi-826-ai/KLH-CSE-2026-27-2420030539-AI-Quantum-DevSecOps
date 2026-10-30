# Phase 5 Cryptographic Agility

## Purpose

The policy engine returns a versioned profile name. `CryptoProfileFactory`
maps that exact name to interoperable key-establishment, payload-encryption,
and signature providers. Unknown names fail closed.

| Policy profile | Key establishment | Payload protection | Sender signature |
|---|---|---|---|
| Classical | X25519 | AES-256-GCM | ECDSA P-256 with SHA-256 |
| Hybrid | X-Wing (X25519 plus ML-KEM-768) | AES-256-GCM | ML-DSA-65 |
| Post-quantum | ML-KEM-768 | AES-256-GCM | ML-DSA-65 |

Every secure envelope authenticates the encapsulation, nonce, ciphertext, and
associated data. Policy decision IDs and correlation IDs should be supplied as
associated data by consuming services so ciphertext cannot be moved silently
between request contexts.

## Standards and implementation boundary

- ML-KEM follows NIST FIPS 203.
- ML-DSA follows NIST FIPS 204.
- The implementation uses Java 21 JCA/JCE and Bouncy Castle 1.86.
- AES-GCM uses a fresh 96-bit nonce and a 128-bit authentication tag.
- Shared secrets are domain-separated through HKDF-SHA-256 before AES use;
  hybrid KEM composition is the maintained Bouncy Castle X-Wing implementation.
- No private key is persisted by this library. Production key storage and
  rotation require a keystore or KMS boundary in a later deployment phase.
- This research prototype is not a FIPS 140-validated cryptographic module.

Official references:

- https://csrc.nist.gov/pubs/fips/203/final
- https://csrc.nist.gov/pubs/fips/204/final
- https://www.bouncycastle.org/download/bouncy-castle-java/

## Evidence

Correctness tests cover key agreement/encapsulation, encryption round trips,
signature verification, tampered ciphertext, changed messages, wrong associated
data, and unknown policy profiles. JMH benchmarks measure AES-GCM encryption,
X25519, ML-KEM-768, the hybrid KEM, and ML-DSA-65 signing independently.
