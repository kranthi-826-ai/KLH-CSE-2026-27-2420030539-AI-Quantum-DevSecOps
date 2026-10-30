package com.pqc.security.crypto.api;

public record EncryptedPayload(byte[] nonce, byte[] ciphertext) {
    public EncryptedPayload {
        nonce = nonce.clone();
        ciphertext = ciphertext.clone();
    }

    @Override public byte[] nonce() { return nonce.clone(); }
    @Override public byte[] ciphertext() { return ciphertext.clone(); }
}
