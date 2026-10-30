package com.pqc.security.crypto.benchmark;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class EnvelopeBenchmarkTests {
    @Test void allModesExecuteTheSamePayloadBoundary() throws Exception {
        for (String mode : new String[]{"CLASSICAL", "HYBRID", "PQC"}) {
            var input = new EnvelopeBenchmark.Inputs(); input.mode = mode; input.setup();
            var envelope = new EnvelopeBenchmark().freshKeyRoundTrip(input);
            assertEquals(4096, input.payload.length);
            assertEquals(4112, envelope.payload().ciphertext().length);
            assertEquals(12, envelope.payload().nonce().length);
            assertTrue(envelope.encapsulation().length > 0);
            assertTrue(envelope.signature().length > 0);
        }
    }
    @Test void unrecognizedModeFailsBeforeMeasurement() {
        var input = new EnvelopeBenchmark.Inputs(); input.mode = "UNKNOWN";
        assertThrows(IllegalArgumentException.class, input::setup);
    }
}
