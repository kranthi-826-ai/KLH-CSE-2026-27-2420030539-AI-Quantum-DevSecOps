package com.pqc.security.crypto.classical;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.EncryptedPayload;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class ClassicalCryptoTests {
    @Test void x25519EncapsulationProducesSameSecret() throws Exception {
        X25519KemProvider kem = new X25519KemProvider();
        CryptoKeyPair recipient = kem.generateKeyPair();
        Encapsulation sender = kem.encapsulate(recipient.publicKey());
        assertArrayEquals(sender.sharedSecret(), kem.decapsulate(recipient.privateKey(), sender.ciphertext()));
    }

    @Test void aesGcmRoundTripAndTamperDetection() throws Exception {
        AesGcmPayloadCipher cipher = new AesGcmPayloadCipher();
        byte[] key = new byte[32];
        byte[] aad = "policy-1.1.0".getBytes(StandardCharsets.UTF_8);
        EncryptedPayload encrypted = cipher.encrypt(key, "protected".getBytes(StandardCharsets.UTF_8), aad);
        assertEquals("protected", new String(cipher.decrypt(key, encrypted, aad), StandardCharsets.UTF_8));
        byte[] tampered = encrypted.ciphertext();
        tampered[0] ^= 1;
        assertThrows(Exception.class, () -> cipher.decrypt(key,
                new EncryptedPayload(encrypted.nonce(), tampered), aad));
    }

    @Test void ecdsaRejectsChangedMessage() throws Exception {
        EcdsaP256SignatureProvider signatures = new EcdsaP256SignatureProvider();
        CryptoKeyPair keys = signatures.generateKeyPair();
        byte[] message = "message".getBytes(StandardCharsets.UTF_8);
        byte[] signature = signatures.sign(keys.privateKey(), message);
        assertTrue(signatures.verify(keys.publicKey(), message, signature));
        assertFalse(signatures.verify(keys.publicKey(), "changed".getBytes(StandardCharsets.UTF_8), signature));
    }
}
