package com.pqc.security.crypto.classical;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.KemProvider;

import javax.crypto.KeyAgreement;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;

public final class X25519KemProvider implements KemProvider {
    @Override public String algorithm() { return "X25519"; }

    @Override
    public CryptoKeyPair generateKeyPair() throws GeneralSecurityException {
        KeyPair pair = KeyPairGenerator.getInstance("X25519").generateKeyPair();
        return new CryptoKeyPair(pair.getPublic().getEncoded(), pair.getPrivate().getEncoded());
    }

    @Override
    public Encapsulation encapsulate(byte[] recipientPublicKey) throws GeneralSecurityException {
        KeyPair ephemeral = KeyPairGenerator.getInstance("X25519").generateKeyPair();
        PublicKey recipient = KeyFactory.getInstance("X25519")
                .generatePublic(new X509EncodedKeySpec(recipientPublicKey));
        return new Encapsulation(ephemeral.getPublic().getEncoded(),
                agree(ephemeral.getPrivate(), recipient));
    }

    @Override
    public byte[] decapsulate(byte[] recipientPrivateKey, byte[] encapsulation)
            throws GeneralSecurityException {
        KeyFactory factory = KeyFactory.getInstance("X25519");
        PrivateKey recipient = factory.generatePrivate(new PKCS8EncodedKeySpec(recipientPrivateKey));
        PublicKey ephemeral = factory.generatePublic(new X509EncodedKeySpec(encapsulation));
        return agree(recipient, ephemeral);
    }

    private static byte[] agree(PrivateKey privateKey, PublicKey publicKey)
            throws GeneralSecurityException {
        KeyAgreement agreement = KeyAgreement.getInstance("X25519");
        agreement.init(privateKey);
        agreement.doPhase(publicKey, true);
        return agreement.generateSecret();
    }
}
