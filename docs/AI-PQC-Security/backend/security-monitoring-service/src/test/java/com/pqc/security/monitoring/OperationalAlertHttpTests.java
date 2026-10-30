package com.pqc.security.monitoring;

import com.sun.net.httpserver.HttpServer;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.concurrent.atomic.*;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OperationalAlertHttpTests {
    static HttpServer upstream;
    static AtomicInteger calls = new AtomicInteger();
    static AtomicReference<String> mode = new AtomicReference<>("good");
    static {
        try {
            upstream = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            upstream.createContext("/api/v1/alerts", exchange -> {
                calls.incrementAndGet();
                String body = switch (mode.get()) {
                    case "broken" -> "private-upstream-invalid-json";
                    case "huge" -> "x".repeat(1_048_577);
                    case "invalidState" -> "{\"status\":\"success\",\"data\":{\"alerts\":[{\"labels\":{\"alertname\":\"AuditOutboxDeadEvents\"},\"state\":\"unexpected\"}]}}";
                    case "auditFailure" -> "{\"status\":\"success\",\"data\":{\"alerts\":[{\"labels\":{\"alertname\":\"AdaptiveAuditWriteFailure\",\"application\":\"business-service\"},\"state\":\"firing\"},{\"labels\":{\"alertname\":\"AdaptiveAuditMetricUnavailable\"},\"state\":\"pending\"}]}}";
                    default -> "{\"status\":\"success\",\"data\":{\"alerts\":[{\"labels\":{\"alertname\":\"AuditOutboxDeadEvents\",\"application\":\"auth-service\",\"instance\":\"auth-service:8081\",\"severity\":\"critical\",\"secretUnusedLabel\":\"must-not-forward\"},\"state\":\"firing\",\"activeAt\":\"2026-10-20T12:00:00Z\",\"annotations\":{\"summary\":\"Needs recovery\"}},{\"labels\":{\"alertname\":\"UnrelatedAlert\"},\"state\":\"firing\"}]}}";
                };
                byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, bytes.length);
                try (var stream = exchange.getResponseBody()) { stream.write(bytes); }
            });
            upstream.start();
        } catch (Exception error) { throw new ExceptionInInitializerError(error); }
    }
    @DynamicPropertySource static void source(DynamicPropertyRegistry values) {
        values.add("monitoring.prometheus.url", () -> "http://127.0.0.1:" + upstream.getAddress().getPort());
    }
    @AfterAll static void stop() { upstream.stop(0); }
    @BeforeEach void reset() { mode.set("good"); calls.set(0); }
    @Value("${local.server.port}") int port;
    @Value("${security.jwt.secret}") String secret;
    HttpResponse<String> get(String role) throws Exception {
        var request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/events/operations/alerts"));
        if (role != null) request.header("Authorization", "Bearer " + Jwts.builder().subject("test-operator").claim("role", role)
                .expiration(new Date(System.currentTimeMillis() + 60000))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).compact());
        return HttpClient.newHttpClient().send(request.GET().build(), HttpResponse.BodyHandlers.ofString());
    }
    @Test void permissionsPrecedeUpstreamAccessAndOnlyKnownSafeFieldsAreReturned() throws Exception {
        assertThat(get(null).statusCode()).isEqualTo(401);
        assertThat(get("ROLE_USER").statusCode()).isEqualTo(403);
        assertThat(calls.get()).isZero();
        var admin = get("ROLE_ADMIN");
        assertThat(admin.statusCode()).isEqualTo(200);
        assertThat(admin.body()).contains("Prometheus", "firing", "Needs recovery", "AuditOutboxDeadEvents")
                .doesNotContain("must-not-forward", "UnrelatedAlert");
        assertThat(admin.headers().firstValue("Cache-Control")).contains("no-store");
    }
    @Test void reviewedAdaptiveAuditAlertsReachAuthorizedOperators() throws Exception {
        mode.set("auditFailure");
        assertThat(get("ROLE_USER").statusCode()).isEqualTo(403);
        assertThat(calls.get()).isZero();
        var result = get("ROLE_ADMIN");
        assertThat(result.statusCode()).isEqualTo(200);
        assertThat(result.body()).contains("AdaptiveAuditWriteFailure", "AdaptiveAuditMetricUnavailable",
                "business-service", "firing", "pending");
    }
    @Test void invalidAndOversizedUpstreamResponsesBecomeUnknownNotHealthy() throws Exception {
        for (String value : new String[]{"broken", "huge", "invalidState"}) {
            mode.set(value);
            var response = get("ROLE_ADMIN");
            assertThat(response.statusCode()).isEqualTo(503);
            assertThat(response.body()).contains("alert state is unknown").doesNotContain("private-upstream", "Exception");
        }
    }
}
