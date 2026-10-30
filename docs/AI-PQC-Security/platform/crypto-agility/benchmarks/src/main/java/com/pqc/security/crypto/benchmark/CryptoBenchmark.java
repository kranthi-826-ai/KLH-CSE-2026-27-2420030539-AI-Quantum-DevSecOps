package com.pqc.security.crypto.benchmark;

import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.classical.AesGcmPayloadCipher;
import com.pqc.security.crypto.classical.X25519KemProvider;
import com.pqc.security.crypto.hybrid.XWingHybridProvider;
import com.pqc.security.crypto.pqc.MlDsa65SignatureProvider;
import com.pqc.security.crypto.pqc.MlKem768Provider;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
public class CryptoBenchmark {
    @State(Scope.Thread)
    public static class Inputs {
        final AesGcmPayloadCipher aes = new AesGcmPayloadCipher();
        final X25519KemProvider x25519 = new X25519KemProvider();
        final MlKem768Provider mlKem = new MlKem768Provider();
        final XWingHybridProvider hybrid = new XWingHybridProvider();
        final MlDsa65SignatureProvider mlDsa = new MlDsa65SignatureProvider();
        final byte[] payload = new byte[4096];
        final byte[] aad = "benchmark-policy-v1".getBytes(StandardCharsets.UTF_8);
        final byte[] aesKey = new byte[32];
        CryptoKeyPair x25519Keys;
        CryptoKeyPair mlKemKeys;
        CryptoKeyPair hybridKeys;
        CryptoKeyPair mlDsaKeys;

        @Setup(Level.Trial)
        public void setup() throws Exception {
            x25519Keys = x25519.generateKeyPair();
            mlKemKeys = mlKem.generateKeyPair();
            hybridKeys = hybrid.generateKeyPair();
            mlDsaKeys = mlDsa.generateKeyPair();
        }
    }

    @Benchmark public Object aesGcmEncrypt4KiB(Inputs input) throws Exception {
        return input.aes.encrypt(input.aesKey, input.payload, input.aad);
    }
    @Benchmark public Object x25519Encapsulate(Inputs input) throws Exception {
        return input.x25519.encapsulate(input.x25519Keys.publicKey());
    }
    @Benchmark public Object mlKem768Encapsulate(Inputs input) throws Exception {
        return input.mlKem.encapsulate(input.mlKemKeys.publicKey());
    }
    @Benchmark public Object hybridEncapsulate(Inputs input) throws Exception {
        return input.hybrid.encapsulate(input.hybridKeys.publicKey());
    }
    @Benchmark public Object mlDsa65Sign4KiB(Inputs input) throws Exception {
        return input.mlDsa.sign(input.mlDsaKeys.privateKey(), input.payload);
    }
}
