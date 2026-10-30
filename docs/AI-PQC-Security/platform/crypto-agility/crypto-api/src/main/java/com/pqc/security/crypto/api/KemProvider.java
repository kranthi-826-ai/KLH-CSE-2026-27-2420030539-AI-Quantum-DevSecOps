package com.pqc.security.crypto.api;

import java.security.GeneralSecurityException;

public interface KemProvider {
    String algorithm();
    CryptoKeyPair generateKeyPair() throws GeneralSecurityException;
    Encapsulation encapsulate(byte[] recipientPublicKey) throws GeneralSecurityException;
    byte[] decapsulate(byte[] recipientPrivateKey, byte[] encapsulation) throws GeneralSecurityException;
}
