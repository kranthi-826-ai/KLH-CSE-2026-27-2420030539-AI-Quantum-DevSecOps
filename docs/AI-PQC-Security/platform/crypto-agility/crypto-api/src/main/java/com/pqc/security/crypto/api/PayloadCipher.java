package com.pqc.security.crypto.api;

import java.security.GeneralSecurityException;

public interface PayloadCipher {
    String algorithm();
    EncryptedPayload encrypt(byte[] key, byte[] plaintext, byte[] associatedData)
            throws GeneralSecurityException;
    byte[] decrypt(byte[] key, EncryptedPayload payload, byte[] associatedData)
            throws GeneralSecurityException;
}
