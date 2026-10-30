package com.pqc.security.policy.service;

import com.pqc.security.policy.domain.DataSensitivity;
import com.pqc.security.policy.dto.NetworkPolicyRequest;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.web.server.ResponseStatusException;
import static org.junit.jupiter.api.Assertions.*;

/** Negative-only HTTP fixtures test the dependency contract, not detection accuracy. */
class AiRiskClientResponseTests {
    private static final String VALID = """
        {"predicted_attack":false,"risk_score":0.2,"risk_level":"LOW",
         "model_version":"0123456789abcdef","model_name":"fixture-model",
         "correlation_id":"response-fixture","explanation":"Synthetic contract fixture"}
        """;

    private com.pqc.security.policy.dto.AiPredictionResponse predict(String body) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api/v1/ai/predict", exchange -> {
            exchange.getRequestBody().readAllBytes();
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, bytes.length);
            try (var output = exchange.getResponseBody()) { output.write(bytes); }
            finally { exchange.close(); }
        });
        server.start();
        try {
            return new AiRiskClient("http://127.0.0.1:" + server.getAddress().getPort(), "synthetic-key")
                .predict(new NetworkPolicyRequest(Map.of("dur", 1), DataSensitivity.PUBLIC,
                    true, true, 100, "fixture", "response-fixture"));
        } finally { server.stop(0); }
    }

    @ParameterizedTest
    @ValueSource(strings = {"predicted_attack", "risk_score", "risk_level", "model_version",
        "model_name", "correlation_id", "explanation"})
    void rejectsMissingFieldsAfterActualHttpDeserialization(String field) throws Exception {
        String body = VALID.replaceAll("\"" + field + "\"\\s*:\\s*(\"[^\"]*\"|false|0\\.2),?", "")
            .replaceAll(",\\s*}", "}");
        var error = assertThrows(ResponseStatusException.class, () -> predict(body));
        assertEquals(502, error.getStatusCode().value());
        assertEquals("AI prediction response is invalid", error.getReason());
    }

    @ParameterizedTest
    @ValueSource(strings = {"null", "-0.01", "1.01", "\"NaN\""})
    void rejectsInvalidScores(String score) {
        var error = assertThrows(ResponseStatusException.class,
            () -> predict(VALID.replace("0.2", score)));
        assertEquals(502, error.getStatusCode().value());
    }

    @ParameterizedTest
    @ValueSource(strings = {"LOW:HIGH", "response-fixture:other-request",
        "0123456789abcdef:unknown-version", "fixture-model:invalid model", "LOW:UNKNOWN"})
    void rejectsContradictoryOrInvalidMetadata(String replacement) {
        String[] parts = replacement.split(":", 2);
        var error = assertThrows(ResponseStatusException.class,
            () -> predict(VALID.replace(parts[0], parts[1])));
        assertEquals(502, error.getStatusCode().value());
    }

    @ParameterizedTest
    @ValueSource(strings = {"{}", "null", "[1,2]", "not json"})
    void rejectsMalformedOrEmptyResponses(String body) {
        var error = assertThrows(ResponseStatusException.class, () -> predict(body));
        assertEquals(502, error.getStatusCode().value());
    }

    @ParameterizedTest
    @ValueSource(doubles = {0, .349999, .35, .699999, .70, 1})
    void acceptsValidRiskBoundariesWithoutInventingClassifierThreshold(double score) throws Exception {
        String risk = score >= .70 ? "HIGH" : score >= .35 ? "MEDIUM" : "LOW";
        var response = predict(VALID.replace("0.2", Double.toString(score)).replace("LOW", risk));
        assertEquals(score, response.riskScore());
        assertFalse(response.predictedAttack()); // Classifier label and risk-band thresholds are separate contracts.
    }
}
