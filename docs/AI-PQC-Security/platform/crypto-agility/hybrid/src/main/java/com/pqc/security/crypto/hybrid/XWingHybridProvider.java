package com.pqc.security.crypto.hybrid;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.Encapsulation;
import com.pqc.security.crypto.api.KemProvider;
import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.SecretWithEncapsulation;
import org.bouncycastle.pqc.crypto.xwing.XWingKEMExtractor;
import org.bouncycastle.pqc.crypto.xwing.XWingKEMGenerator;
import org.bouncycastle.pqc.crypto.xwing.XWingKeyGenerationParameters;
import org.bouncycastle.pqc.crypto.xwing.XWingKeyPairGenerator;
import org.bouncycastle.pqc.crypto.xwing.XWingPrivateKeyParameters;
import org.bouncycastle.pqc.crypto.xwing.XWingPublicKeyParameters;

import java.security.GeneralSecurityException;
import java.security.SecureRandom;

public final class XWingHybridProvider implements KemProvider {
    private final SecureRandom random = new SecureRandom();

    @Override public String algorithm() { return "X-Wing"; }

    @Override
    public CryptoKeyPair generateKeyPair() throws GeneralSecurityException {
        XWingKeyPairGenerator generator = new XWingKeyPairGenerator();
        generator.init(new XWingKeyGenerationParameters(random));
        AsymmetricCipherKeyPair pair = generator.generateKeyPair();
        return new CryptoKeyPair(((XWingPublicKeyParameters) pair.getPublic()).getEncoded(),
                ((XWingPrivateKeyParameters) pair.getPrivate()).getEncoded());
    }

    @Override
    public Encapsulation encapsulate(byte[] recipientPublicKey) throws GeneralSecurityException {
        SecretWithEncapsulation secret = new XWingKEMGenerator(random)
                .generateEncapsulated(new XWingPublicKeyParameters(recipientPublicKey));
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
            return new XWingKEMExtractor(new XWingPrivateKeyParameters(recipientPrivateKey))
                    .extractSecret(encapsulation);
        } catch (RuntimeException exception) {
            throw new GeneralSecurityException("X-Wing decapsulation failed", exception);
        }
    }
}
