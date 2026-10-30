package com.pqc.security.crypto.api;

public final class CryptoProfiles {
    public static final String CLASSICAL = "X25519+AES-256-GCM+ECDSA-P256";
    public static final String HYBRID = "X-Wing+AES-256-GCM+ML-DSA-65";
    public static final String PQC = "ML-KEM-768+AES-256-GCM+ML-DSA-65";

    private CryptoProfiles() { }
}
