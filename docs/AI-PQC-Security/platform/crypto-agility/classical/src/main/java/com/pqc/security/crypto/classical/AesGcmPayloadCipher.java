package com.pqc.security.crypto.classical;

import com.pqc.security.crypto.api.EncryptedPayload;
import com.pqc.security.crypto.api.PayloadCipher;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.security.GeneralSecurityException;
import java.security.SecureRandom;

public final class AesGcmPayloadCipher implements PayloadCipher {
    private static final int KEY_BYTES = 32;
    private static final int NONCE_BYTES = 12;
    private static final int TAG_BITS = 128;
    private final SecureRandom random;

    public AesGcmPayloadCipher() { this(new SecureRandom()); }
    AesGcmPayloadCipher(SecureRandom random) { this.random = random; }

    @Override public String algorithm() { return "AES-256-GCM"; }

    @Override
    public EncryptedPayload encrypt(byte[] key, byte[] plaintext, byte[] associatedData)
            throws GeneralSecurityException {
        validateKey(key);
        byte[] nonce = new byte[NONCE_BYTES];
        random.nextBytes(nonce);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"),
                new GCMParameterSpec(TAG_BITS, nonce));
        if (associatedData != null) cipher.updateAAD(associatedData);
        return new EncryptedPayload(nonce, cipher.doFinal(plaintext));
    }

    @Override
    public byte[] decrypt(byte[] key, EncryptedPayload payload, byte[] associatedData)
            throws GeneralSecurityException {
        validateKey(key);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"),
                new GCMParameterSpec(TAG_BITS, payload.nonce()));
        if (associatedData != null) cipher.updateAAD(associatedData);
        return cipher.doFinal(payload.ciphertext());
    }

    private static void validateKey(byte[] key) {
        if (key == null || key.length != KEY_BYTES) {
            throw new IllegalArgumentException("AES-256-GCM requires a 32-byte key");
        }
    }
}
