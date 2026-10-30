package com.pqc.security.crypto.hybrid;

import com.pqc.security.crypto.classical.AesGcmPayloadCipher;
import com.pqc.security.crypto.classical.EcdsaP256SignatureProvider;
import com.pqc.security.crypto.classical.X25519KemProvider;
import com.pqc.security.crypto.pqc.MlDsa65SignatureProvider;
import com.pqc.security.crypto.pqc.MlKem768Provider;

import static com.pqc.security.crypto.api.CryptoProfiles.CLASSICAL;
import static com.pqc.security.crypto.api.CryptoProfiles.HYBRID;
import static com.pqc.security.crypto.api.CryptoProfiles.PQC;

public final class CryptoProfileFactory {
    private CryptoProfileFactory() { }

    public static CryptoProfile create(String profile) {
        return switch (profile) {
            case CLASSICAL -> new CryptoProfile(profile, new X25519KemProvider(),
                    new AesGcmPayloadCipher(), new EcdsaP256SignatureProvider());
            case HYBRID -> new CryptoProfile(profile, new XWingHybridProvider(),
                    new AesGcmPayloadCipher(), new MlDsa65SignatureProvider());
            case PQC -> new CryptoProfile(profile, new MlKem768Provider(),
                    new AesGcmPayloadCipher(), new MlDsa65SignatureProvider());
            default -> throw new IllegalArgumentException("Unsupported cryptographic profile: " + profile);
        };
    }
}
