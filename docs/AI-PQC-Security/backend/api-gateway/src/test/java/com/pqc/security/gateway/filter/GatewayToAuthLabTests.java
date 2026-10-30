package com.pqc.security.gateway.filter;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import static org.assertj.core.api.Assertions.assertThat;

/** No downstream fixtures: routes to a separately running real Auth Service/H2. */
@EnabledIfSystemProperty(named = "routed.auth.url", matches = "http://127\\.0\\.0\\.1:[0-9]+")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
    "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false", "security.shadow.enabled=true",
    "security.shadow.expose-observation-id=true", "security.shadow.max-events-per-peer=512",
    "security.rate-limit.api-capacity=5000", "security.rate-limit.auth-capacity=5000",
    "spring.cloud.gateway.server.webmvc.routes[0].id=real-auth-lab",
    "spring.cloud.gateway.server.webmvc.routes[0].predicates[0]=Path=/api/v1/auth/**"})
class GatewayToAuthLabTests {
    @DynamicPropertySource static void properties(DynamicPropertyRegistry properties) {
        properties.add("spring.cloud.gateway.server.webmvc.routes[0].id", () -> "real-auth-lab");
        properties.add("spring.cloud.gateway.server.webmvc.routes[0].predicates[0]", () -> "Path=/api/v1/auth/**");
        properties.add("spring.cloud.gateway.server.webmvc.routes[0].uri", () -> System.getProperty("routed.auth.url"));
        properties.add("security.shadow.output", () -> Path.of(System.getProperty("routed.output"), "gateway.jsonl").toString());
        properties.add("security.shadow.feature-version", () -> Boolean.getBoolean("routed.rich") ? "v2" : "v1");
    }
    @Value("${local.server.port}") private int port;
    @Autowired private ShadowObservationWriter writer;
    @Test void collectRealRoutedSessions() throws Exception {
        Path root = Path.of(System.getProperty("routed.root"));
        Path output = Path.of(System.getProperty("routed.output"));
        var arguments = new java.util.ArrayList<>(java.util.List.of(System.getProperty("routed.python"),
            root.resolve("ml/data/collect_microservice_sessions.py").toString(), "--base-url", "http://127.0.0.1:" + port,
            "--output", output.resolve("raw").toString(), "--routed"));
        if (Boolean.getBoolean("routed.rich")) {
            arguments.add("--rich"); arguments.add("--seed"); arguments.add("20261021");
        }
        var process = new ProcessBuilder(arguments)
            .redirectErrorStream(true).redirectOutput(output.resolve("collector.log").toFile()).start();
        try {
            assertThat(process.waitFor(300, TimeUnit.SECONDS)).isTrue();
            assertThat(process.exitValue()).withFailMessage(Files.readString(output.resolve("collector.log"))).isZero();
        } finally {
            if (process.isAlive()) process.destroyForcibly();
            writer.close();
        }
        assertThat(Files.readString(output.resolve("raw/manifest.json"))).contains("\"status\": \"complete\"");
    }
}
