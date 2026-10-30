package com.pqc.security.crypto.pqc;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.KemProvider;
import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.SecretWithEncapsulation;
import org.bouncycastle.crypto.generators.MLKEMKeyPairGenerator;
import org.bouncycastle.crypto.kems.MLKEMExtractor;
import org.bouncycastle.crypto.kems.MLKEMGenerator;
import org.bouncycastle.crypto.params.MLKEMKeyGenerationParameters;
import org.bouncycastle.crypto.params.MLKEMParameters;
import org.bouncycastle.crypto.params.MLKEMPrivateKeyParameters;
import org.bouncycastle.crypto.params.MLKEMPublicKeyParameters;

import java.security.GeneralSecurityException;
import java.security.SecureRandom;

public final class MlKem768Provider implements KemProvider {
    private static final MLKEMParameters PARAMETERS = MLKEMParameters.ml_kem_768;
    private final SecureRandom random = new SecureRandom();

    @Override public String algorithm() { return "ML-KEM-768"; }

    @Override
    public CryptoKeyPair generateKeyPair() {
        MLKEMKeyPairGenerator generator = new MLKEMKeyPairGenerator();
        generator.init(new MLKEMKeyGenerationParameters(random, PARAMETERS));
        AsymmetricCipherKeyPair pair = generator.generateKeyPair();
        return new CryptoKeyPair(
                ((MLKEMPublicKeyParameters) pair.getPublic()).getEncoded(),
                ((MLKEMPrivateKeyParameters) pair.getPrivate()).getEncoded());
    }

    @Override
    public Encapsulation encapsulate(byte[] recipientPublicKey) {
        MLKEMPublicKeyParameters publicKey = new MLKEMPublicKeyParameters(PARAMETERS, recipientPublicKey);
        SecretWithEncapsulation secret = new MLKEMGenerator(random).generateEncapsulated(publicKey);
        try {
            return new Encapsulation(secret.getEncapsulation(), secret.getSecret());
        } finally {
            try { secret.destroy(); } catch (Exception ignored) { }
        }
    }

    @Override
    public byte[] decapsulate(byte[] recipientPrivateKey, byte[] encapsulation)
            throws GeneralSecurityException {
        try {
            return new MLKEMExtractor(new MLKEMPrivateKeyParameters(PARAMETERS, recipientPrivateKey))
                    .extractSecret(encapsulation);
        } catch (RuntimeException exception) {
            throw new GeneralSecurityException("ML-KEM-768 decapsulation failed", exception);
        }
    }
}
