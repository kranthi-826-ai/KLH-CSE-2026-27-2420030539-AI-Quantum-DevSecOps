package com.pqc.security.crypto.pqc;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class PqcCryptoTests {
    @Test void mlKem768RoundTrip() throws Exception {
        MlKem768Provider kem = new MlKem768Provider();
        CryptoKeyPair keys = kem.generateKeyPair();
        Encapsulation sender = kem.encapsulate(keys.publicKey());
        assertArrayEquals(sender.sharedSecret(), kem.decapsulate(keys.privateKey(), sender.ciphertext()));
    }

    @Test void mlDsa65SignsAndRejectsChangedMessage() throws Exception {
        MlDsa65SignatureProvider signatures = new MlDsa65SignatureProvider();
        CryptoKeyPair keys = signatures.generateKeyPair();
        byte[] message = "pqc-message".getBytes(StandardCharsets.UTF_8);
        byte[] signature = signatures.sign(keys.privateKey(), message);
        assertTrue(signatures.verify(keys.publicKey(), message, signature));
        assertFalse(signatures.verify(keys.publicKey(), "changed".getBytes(StandardCharsets.UTF_8), signature));
    }
}
