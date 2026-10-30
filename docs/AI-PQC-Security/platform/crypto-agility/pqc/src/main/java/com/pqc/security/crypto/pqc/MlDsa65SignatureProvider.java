package com.pqc.security.crypto.pqc;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.SignatureProvider;
import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.CryptoException;
import org.bouncycastle.crypto.generators.MLDSAKeyPairGenerator;
import org.bouncycastle.crypto.params.MLDSAKeyGenerationParameters;
import org.bouncycastle.crypto.params.MLDSAParameters;
import org.bouncycastle.crypto.params.MLDSAPrivateKeyParameters;
import org.bouncycastle.crypto.params.MLDSAPublicKeyParameters;
import org.bouncycastle.crypto.signers.MLDSASigner;

import java.security.GeneralSecurityException;
import java.security.SecureRandom;

public final class MlDsa65SignatureProvider implements SignatureProvider {
    private static final MLDSAParameters PARAMETERS = MLDSAParameters.ml_dsa_65;
    private final SecureRandom random = new SecureRandom();

    @Override public String algorithm() { return "ML-DSA-65"; }

    @Override
    public CryptoKeyPair generateKeyPair() {
        MLDSAKeyPairGenerator generator = new MLDSAKeyPairGenerator();
        generator.init(new MLDSAKeyGenerationParameters(random, PARAMETERS));
        AsymmetricCipherKeyPair pair = generator.generateKeyPair();
        return new CryptoKeyPair(
                ((MLDSAPublicKeyParameters) pair.getPublic()).getEncoded(),
                ((MLDSAPrivateKeyParameters) pair.getPrivate()).getEncoded());
    }

    @Override
    public byte[] sign(byte[] privateKey, byte[] message) throws GeneralSecurityException {
        MLDSASigner signer = new MLDSASigner();
        signer.init(true, new MLDSAPrivateKeyParameters(PARAMETERS, privateKey));
        signer.update(message, 0, message.length);
        try {
            return signer.generateSignature();
        } catch (CryptoException exception) {
            throw new GeneralSecurityException("ML-DSA-65 signing failed", exception);
        }
    }

    @Override
    public boolean verify(byte[] publicKey, byte[] message, byte[] signature)
            throws GeneralSecurityException {
        try {
            MLDSASigner verifier = new MLDSASigner();
            verifier.init(false, new MLDSAPublicKeyParameters(PARAMETERS, publicKey));
            verifier.update(message, 0, message.length);
            return verifier.verifySignature(signature);
        } catch (RuntimeException exception) {
            throw new GeneralSecurityException("ML-DSA-65 verification failed", exception);
        }
    }
}
