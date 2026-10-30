package com.pqc.security.crypto.hybrid;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.SecureEnvelope;
import com.pqc.security.crypto.classical.AesGcmPayloadCipher;
import com.pqc.security.crypto.pqc.MlDsa65SignatureProvider;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;
import static com.pqc.security.crypto.api.CryptoProfiles.*;

class HybridCryptoTests {
    @Test void policyProfilesMapToExecutableProviders() {
        assertEquals("X25519", CryptoProfileFactory.create(CLASSICAL).kem().algorithm());
        assertEquals("X-Wing", CryptoProfileFactory.create(HYBRID).kem().algorithm());
        assertEquals("ML-KEM-768", CryptoProfileFactory.create(PQC).kem().algorithm());
        assertThrows(IllegalArgumentException.class, () -> CryptoProfileFactory.create("unknown"));
    }

    @Test void hybridKemRequiresBothMatchingComponents() throws Exception {
        XWingHybridProvider kem = new XWingHybridProvider();
        CryptoKeyPair keys = kem.generateKeyPair();
        Encapsulation sender = kem.encapsulate(keys.publicKey());
        assertArrayEquals(sender.sharedSecret(), kem.decapsulate(keys.privateKey(), sender.ciphertext()));
    }

    @Test void signedEncryptedEnvelopeRoundTripAndTamperRejection() throws Exception {
        XWingHybridProvider kem = new XWingHybridProvider();
        MlDsa65SignatureProvider signatures = new MlDsa65SignatureProvider();
        SecureEnvelopeService service = new SecureEnvelopeService(kem, new AesGcmPayloadCipher(), signatures);
        CryptoKeyPair recipient = kem.generateKeyPair();
        CryptoKeyPair sender = signatures.generateKeyPair();
        byte[] aad = "decision-id:123".getBytes(StandardCharsets.UTF_8);
        SecureEnvelope envelope = service.seal(recipient.publicKey(), sender.privateKey(),
                "sensitive-data".getBytes(StandardCharsets.UTF_8), aad);
        assertEquals("sensitive-data", new String(service.open(recipient.privateKey(),
                sender.publicKey(), envelope, aad), StandardCharsets.UTF_8));
        assertThrows(Exception.class, () -> service.open(recipient.privateKey(),
                sender.publicKey(), envelope, "wrong-context".getBytes(StandardCharsets.UTF_8)));
        SecureEnvelope alteredMetadata = new SecureEnvelope("ML-KEM-768", envelope.cipherAlgorithm(),
                envelope.signatureAlgorithm(), envelope.encapsulation(), envelope.payload(), envelope.signature());
        assertThrows(Exception.class, () -> service.open(recipient.privateKey(),
                sender.publicKey(), alteredMetadata, aad));
    }
}
