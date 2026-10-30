package com.pqc.security.crypto.api;

public record SecureEnvelope(
        String kemAlgorithm,
        String cipherAlgorithm,
        String signatureAlgorithm,
        byte[] encapsulation,
        EncryptedPayload payload,
        byte[] signature) {
    public SecureEnvelope {
        encapsulation = encapsulation.clone();
        signature = signature.clone();
    }

    @Override public byte[] encapsulation() { return encapsulation.clone(); }
    @Override public byte[] signature() { return signature.clone(); }
}
