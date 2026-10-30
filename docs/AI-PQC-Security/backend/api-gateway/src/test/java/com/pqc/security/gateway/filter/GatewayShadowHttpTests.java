package com.pqc.security.gateway.filter;

import com.pqc.security.gateway.ApiGatewayApplication;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerResponse;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(classes = {ApiGatewayApplication.class, GatewayShadowHttpTests.Probes.class},
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false", "security.shadow.enabled=true",
        "security.rate-limit.api-capacity=20", "security.rate-limit.auth-capacity=3",
        "security.rate-limit.auth-period-seconds=3600",
        "spring.cloud.gateway.server.webmvc.routes[0].id=shadow-unused",
        "spring.cloud.gateway.server.webmvc.routes[0].uri=http://127.0.0.1:1",
        "spring.cloud.gateway.server.webmvc.routes[0].predicates[0]=Path=/unused/**"})
class GatewayShadowHttpTests {
    private static final Path OUTPUT;
    static {
        try {
            String explicit = System.getProperty("shadow.test.output");
            OUTPUT = explicit == null ? Files.createTempDirectory("gateway-shadow-").resolve("observations.jsonl") : Path.of(explicit);
        } catch (Exception exception) { throw new ExceptionInInitializerError(exception); }
    }
    @DynamicPropertySource static void output(DynamicPropertyRegistry properties) {
        properties.add("security.shadow.output", OUTPUT::toString);
    }
    @Value("${local.server.port}") private int port;
    @Autowired private ShadowObservationWriter writer;

    @Test void shadowDoesNotChangeResponsesAndCannotBypassRateLimits() throws Exception {
        var client = HttpClient.newHttpClient();
        for (int i = 0; i < 4; i++) {
            var response = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/auth/login"))
                    .header("X-Forwarded-For", "198.51.100." + i)
                    .header("X-Session-ID", "spoofed-" + i)
                    .header("X-Shadow-Observation-ID", "caller-must-not-choose-join-id")
                    .header("Authorization", "Bearer secret-not-for-logs")
                    .POST(HttpRequest.BodyPublishers.ofString("private-password-not-for-logs")).build(),
                    HttpResponse.BodyHandlers.ofString());
            assertThat(response.statusCode()).isEqualTo(i < 3 ? 401 : 429);
            assertThat(response.headers().firstValue("X-Shadow-Observation-ID")).isEmpty();
            if (i == 3) assertThat(response.headers().firstValue("Retry-After")).isPresent();
        }
        var normal = client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/auth/me")).GET().build(),
                HttpResponse.BodyHandlers.ofString());
        assertThat(normal.statusCode()).isEqualTo(200);
        writer.close();
        var lines = Files.readAllLines(OUTPUT);
        assertThat(lines).hasSize(5);
        String contents = String.join("\n", lines);
        assertThat(contents).doesNotContain("private-password", "secret-not-for-logs", "198.51.100", "127.0.0.1", "spoofed");
        assertThat(contents).contains("\"shadow_only\":true", "\"status\":429", "\"prior_failed_login_5s\":3.0");
        assertThat(lines.getFirst()).contains("\"prior_401_5s\":0.0");
    }
    @TestConfiguration static class Probes {
        @Bean RouterFunction<ServerResponse> probeHandlers() {
            // Test-only downstream fixtures: real gateway HTTP/filter behavior, not an auth accuracy study.
            return RouterFunctions.route().POST("/api/v1/auth/login", request -> ServerResponse.status(401).body(Map.of("message", "test rejection")))
                .GET("/api/v1/auth/me", request -> ServerResponse.ok().body(Map.of("message", "test normal"))).build();
        }
    }
}
