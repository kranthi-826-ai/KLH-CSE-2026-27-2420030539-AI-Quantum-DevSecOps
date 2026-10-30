package com.pqc.security.crypto.hybrid;

import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.EncryptedPayload;
import com.pqc.security.crypto.api.KemProvider;
import com.pqc.security.crypto.api.PayloadCipher;
import com.pqc.security.crypto.api.SecureEnvelope;
import com.pqc.security.crypto.api.SignatureProvider;

import java.security.GeneralSecurityException;

public final class SecureEnvelopeService {
    private static final String CONTEXT = "AI-PQC-secure-envelope-v1";
    private final KemProvider kem;
    private final PayloadCipher cipher;
    private final SignatureProvider signatures;

    public SecureEnvelopeService(KemProvider kem, PayloadCipher cipher, SignatureProvider signatures) {
        this.kem = kem;
        this.cipher = cipher;
        this.signatures = signatures;
    }

    public SecureEnvelope seal(byte[] recipientPublicKey, byte[] senderSigningPrivateKey,
                               byte[] plaintext, byte[] associatedData) throws GeneralSecurityException {
        Encapsulation encapsulation = kem.encapsulate(recipientPublicKey);
        byte[] sharedSecret = encapsulation.sharedSecret();
        byte[] key = KeyDerivation.derive(sharedSecret, CONTEXT);
        try {
            EncryptedPayload payload = cipher.encrypt(key, plaintext, associatedData);
            byte[] signed = signedBytes(kem.algorithm(), cipher.algorithm(), signatures.algorithm(),
                    encapsulation.ciphertext(), payload, associatedData);
            return new SecureEnvelope(kem.algorithm(), cipher.algorithm(), signatures.algorithm(),
                    encapsulation.ciphertext(), payload,
                    signatures.sign(senderSigningPrivateKey, signed));
        } finally {
            java.util.Arrays.fill(sharedSecret, (byte) 0);
            java.util.Arrays.fill(key, (byte) 0);
        }
    }

    public byte[] open(byte[] recipientPrivateKey, byte[] senderSigningPublicKey,
                       SecureEnvelope envelope, byte[] associatedData) throws GeneralSecurityException {
        ensureAlgorithms(envelope);
        byte[] signed = signedBytes(envelope.kemAlgorithm(), envelope.cipherAlgorithm(),
                envelope.signatureAlgorithm(), envelope.encapsulation(), envelope.payload(), associatedData);
        if (!signatures.verify(senderSigningPublicKey, signed, envelope.signature())) {
            throw new GeneralSecurityException("Envelope signature verification failed");
        }
        byte[] secret = kem.decapsulate(recipientPrivateKey, envelope.encapsulation());
        byte[] key = KeyDerivation.derive(secret, CONTEXT);
        try {
            return cipher.decrypt(key, envelope.payload(), associatedData);
        } finally {
            java.util.Arrays.fill(secret, (byte) 0);
            java.util.Arrays.fill(key, (byte) 0);
        }
    }

    private void ensureAlgorithms(SecureEnvelope envelope) throws GeneralSecurityException {
        if (!kem.algorithm().equals(envelope.kemAlgorithm())
                || !cipher.algorithm().equals(envelope.cipherAlgorithm())
                || !signatures.algorithm().equals(envelope.signatureAlgorithm())) {
            throw new GeneralSecurityException("Envelope algorithm metadata does not match active providers");
        }
    }

    private static byte[] signedBytes(String kemAlgorithm, String cipherAlgorithm,
                                      String signatureAlgorithm, byte[] encapsulation,
                                      EncryptedPayload payload, byte[] aad) {
        byte[] safeAad = aad == null ? new byte[0] : aad;
        byte[] algorithms = BinaryComponents.join(kemAlgorithm.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                BinaryComponents.join(cipherAlgorithm.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                        signatureAlgorithm.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        return BinaryComponents.join(algorithms, BinaryComponents.join(encapsulation,
                BinaryComponents.join(payload.nonce(), BinaryComponents.join(payload.ciphertext(), safeAad))));
    }
}
