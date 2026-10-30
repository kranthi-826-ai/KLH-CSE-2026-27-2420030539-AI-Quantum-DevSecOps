package com.pqc.security.auth.security;

import com.pqc.security.auth.event.SecurityEventPublisher;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import static org.assertj.core.api.Assertions.assertThat;

/** Opt-in multi-session collection; test settings have priority over local MySQL settings. */
@EnabledIfSystemProperty(named = "session.collector.python", matches = ".+")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
    "spring.datasource.url=jdbc:h2:mem:session_lab;MODE=MySQL;DB_CLOSE_DELAY=-1",
    "spring.datasource.driver-class-name=org.h2.Driver", "spring.datasource.username=sa",
    "spring.datasource.password=", "spring.jpa.hibernate.ddl-auto=create-drop", "eureka.client.enabled=false"})
class SessionTrafficCollectionTests {
    @Value("${local.server.port}") private int port;
    @Value("${spring.datasource.url}") private String datasource;
    @MockitoBean private SecurityEventPublisher eventPublisher;

    @Test void collectIndependentAccountsAndChronologicalPartitions() throws Exception {
        assertThat(datasource).startsWith("jdbc:h2:mem:session_lab");
        Path root = Path.of(System.getProperty("session.collector.root")).toAbsolutePath();
        Path output = Path.of(System.getProperty("session.collector.output")).toAbsolutePath();
        assertThat(Files.exists(output)).isFalse();
        Files.createDirectories(output.getParent());
        Path log = output.resolveSibling(output.getFileName() + ".log");
        Process process = new ProcessBuilder(System.getProperty("session.collector.python"),
            root.resolve("ml/data/collect_microservice_sessions.py").toString(),
            "--base-url", "http://127.0.0.1:" + port, "--output", output.toString())
            .redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            assertThat(process.waitFor(240, TimeUnit.SECONDS)).isTrue();
            assertThat(process.exitValue()).withFailMessage(Files.readString(log)).isZero();
            assertThat(Files.readString(output.resolve("manifest.json"))).contains("\"status\": \"complete\"");
        } finally {
            if (process.isAlive()) process.destroyForcibly();
        }
    }
}
