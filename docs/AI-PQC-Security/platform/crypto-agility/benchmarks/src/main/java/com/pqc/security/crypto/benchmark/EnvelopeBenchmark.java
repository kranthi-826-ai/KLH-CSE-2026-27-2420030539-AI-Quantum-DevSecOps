package com.pqc.security.crypto.benchmark;

import com.pqc.security.crypto.api.CryptoProfiles;
import com.pqc.security.crypto.api.SecureEnvelope;
import com.pqc.security.crypto.hybrid.CryptoProfile;
import com.pqc.security.crypto.hybrid.CryptoProfileFactory;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

/** Matched Business-Service crypto boundary, not HTTP/AI/policy/database latency. */
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 10, time = 1)
@Fork(5)
public class EnvelopeBenchmark {
    @State(Scope.Thread)
    public static class Inputs {
        @Param({"CLASSICAL", "HYBRID", "PQC"})
        public String mode;
        final byte[] payload = new byte[4096];
        final byte[] aad = ("00000000-0000-0000-0000-000000000001:matched-envelope-fixture:"
                + "00000000-0000-0000-0000-000000000002").getBytes(StandardCharsets.UTF_8);

        @Setup(Level.Trial)
        public void setup() {
            for (int index = 0; index < payload.length; index++) payload[index] = (byte) (index % 251);
            profileName(mode); // Reject unexpected parameter values before measurement.
        }
    }

    static String profileName(String mode) {
        return switch (mode) {
            case "CLASSICAL" -> CryptoProfiles.CLASSICAL;
            case "HYBRID" -> CryptoProfiles.HYBRID;
            case "PQC" -> CryptoProfiles.PQC;
            default -> throw new IllegalArgumentException("Unsupported benchmark mode");
        };
    }

    @Benchmark
    public SecureEnvelope freshKeyRoundTrip(Inputs input) throws GeneralSecurityException {
        // Same boundary as AdaptiveSecurityService: provider construction and both
        // fresh key pairs are inside the timed operation, not amortized out.
        CryptoProfile profile = CryptoProfileFactory.create(profileName(input.mode));
        var recipient = profile.kem().generateKeyPair();
        var signer = profile.signatures().generateKeyPair();
        SecureEnvelope envelope = profile.envelopeService().seal(recipient.publicKey(), signer.privateKey(), input.payload, input.aad);
        byte[] opened = profile.envelopeService().open(recipient.privateKey(), signer.publicKey(), envelope, input.aad);
        try {
            if (!MessageDigest.isEqual(input.payload, opened)) {
                throw new GeneralSecurityException("Benchmark round trip did not match");
            }
        } finally { Arrays.fill(opened, (byte) 0); }
        return envelope;
    }

    /** Bounded size samples only; never prints keys, payloads or envelopes. */
    public static void main(String[] args) throws Exception {
        if (args.length != 0) throw new IllegalArgumentException("No size-report arguments supported");
        System.out.println("{\"schema\":\"matched-envelope-sizes-v1\",\"payloadBytes\":4096,\"samplesPerMode\":16,\"modes\":[");
        boolean first = true;
        for (String mode : new String[]{"CLASSICAL", "HYBRID", "PQC"}) {
            Inputs input = new Inputs(); input.mode = mode; input.setup();
            int minimum = Integer.MAX_VALUE, maximum = 0, signatureMin = Integer.MAX_VALUE, signatureMax = 0;
            int encapsulation = 0, nonce = 0, ciphertext = 0;
            for (int sample = 0; sample < 16; sample++) {
                SecureEnvelope envelope = new EnvelopeBenchmark().freshKeyRoundTrip(input);
                encapsulation = envelope.encapsulation().length;
                nonce = envelope.payload().nonce().length;
                ciphertext = envelope.payload().ciphertext().length;
                int signature = envelope.signature().length;
                int bytes = encapsulation + nonce + ciphertext + signature;
                minimum = Math.min(minimum, bytes); maximum = Math.max(maximum, bytes);
                signatureMin = Math.min(signatureMin, signature); signatureMax = Math.max(signatureMax, signature);
            }
            if (!first) System.out.println(","); first = false;
            System.out.printf(Locale.ROOT, "{\"mode\":\"%s\",\"rawComponentsMinBytes\":%d,\"rawComponentsMaxBytes\":%d,"
                + "\"encapsulationBytes\":%d,\"nonceBytes\":%d,\"ciphertextBytes\":%d,\"signatureMinBytes\":%d,\"signatureMaxBytes\":%d}",
                mode, minimum, maximum, encapsulation, nonce, ciphertext, signatureMin, signatureMax);
        }
        System.out.println("\n]}");
    }
}
