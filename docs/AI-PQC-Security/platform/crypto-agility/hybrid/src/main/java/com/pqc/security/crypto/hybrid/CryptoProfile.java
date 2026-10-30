package com.pqc.security.crypto.hybrid;

import com.pqc.security.crypto.api.KemProvider;
import com.pqc.security.crypto.api.PayloadCipher;
import com.pqc.security.crypto.api.SignatureProvider;

public record CryptoProfile(
        String name,
        KemProvider kem,
        PayloadCipher cipher,
        SignatureProvider signatures) {

    public SecureEnvelopeService envelopeService() {
        return new SecureEnvelopeService(kem, cipher, signatures);
    }
}
