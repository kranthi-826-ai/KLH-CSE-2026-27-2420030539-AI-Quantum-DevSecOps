package com.pqc.security.crypto.api;

public record CryptoKeyPair(byte[] publicKey, byte[] privateKey) {
    public CryptoKeyPair {
        publicKey = publicKey.clone();
        privateKey = privateKey.clone();
    }

    @Override public byte[] publicKey() { return publicKey.clone(); }
    @Override public byte[] privateKey() { return privateKey.clone(); }
}
