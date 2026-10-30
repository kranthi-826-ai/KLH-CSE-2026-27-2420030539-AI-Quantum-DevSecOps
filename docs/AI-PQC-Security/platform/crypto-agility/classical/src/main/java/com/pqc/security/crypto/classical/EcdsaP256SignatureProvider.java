package com.pqc.security.crypto.classical;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.SignatureProvider;

import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.Signature;
import java.security.spec.ECGenParameterSpec;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;

public final class EcdsaP256SignatureProvider implements SignatureProvider {
    @Override public String algorithm() { return "SHA256withECDSA-P256"; }

    @Override
    public CryptoKeyPair generateKeyPair() throws GeneralSecurityException {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("EC");
        generator.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair pair = generator.generateKeyPair();
        return new CryptoKeyPair(pair.getPublic().getEncoded(), pair.getPrivate().getEncoded());
    }

    @Override
    public byte[] sign(byte[] privateKey, byte[] message) throws GeneralSecurityException {
        Signature signer = Signature.getInstance("SHA256withECDSA");
        signer.initSign(KeyFactory.getInstance("EC").generatePrivate(new PKCS8EncodedKeySpec(privateKey)));
        signer.update(message);
        return signer.sign();
    }

    @Override
    public boolean verify(byte[] publicKey, byte[] message, byte[] signature)
            throws GeneralSecurityException {
        Signature verifier = Signature.getInstance("SHA256withECDSA");
        verifier.initVerify(KeyFactory.getInstance("EC").generatePublic(new X509EncodedKeySpec(publicKey)));
        verifier.update(message);
        return verifier.verify(signature);
    }
}
