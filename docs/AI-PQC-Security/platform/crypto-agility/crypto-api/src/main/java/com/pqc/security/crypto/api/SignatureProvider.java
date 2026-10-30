package com.pqc.security.crypto.api;

import java.security.GeneralSecurityException;

public interface SignatureProvider {
    String algorithm();
    CryptoKeyPair generateKeyPair() throws GeneralSecurityException;
    byte[] sign(byte[] privateKey, byte[] message) throws GeneralSecurityException;
    boolean verify(byte[] publicKey, byte[] message, byte[] signature) throws GeneralSecurityException;
}
