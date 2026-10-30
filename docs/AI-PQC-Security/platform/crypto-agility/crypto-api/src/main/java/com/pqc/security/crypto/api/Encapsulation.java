package com.pqc.security.crypto.api;

public record Encapsulation(byte[] ciphertext, byte[] sharedSecret) {
    public Encapsulation {
        ciphertext = ciphertext.clone();
        sharedSecret = sharedSecret.clone();
    }

    @Override public byte[] ciphertext() { return ciphertext.clone(); }
    @Override public byte[] sharedSecret() { return sharedSecret.clone(); }
}
