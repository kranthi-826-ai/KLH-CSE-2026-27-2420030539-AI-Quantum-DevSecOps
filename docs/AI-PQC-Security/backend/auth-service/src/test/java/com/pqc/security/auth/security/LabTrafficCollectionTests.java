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

/** Opt-in real HTTP measurements; only test H2 and a stubbed monitoring publisher. */
@EnabledIfSystemProperty(named = "lab.collector.python", matches = ".+")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class LabTrafficCollectionTests {
    @Value("${local.server.port}") private int port;
    @MockitoBean private SecurityEventPublisher eventPublisher;

    @Test void collectBoundedLoopbackObservations() throws Exception {
        Path root = Path.of(System.getProperty("lab.collector.root")).toAbsolutePath();
        Path output = Path.of(System.getProperty("lab.collector.output")).toAbsolutePath();
        Path log = output.resolveSibling(output.getFileName() + ".log");
        assertThat(Files.exists(output)).isFalse();
        Files.createDirectories(output.getParent());
        Process process = new ProcessBuilder(System.getProperty("lab.collector.python"),
            root.resolve("ml/data/collect_microservice_lab.py").toString(),
            "--base-url", "http://127.0.0.1:" + port, "--output", output.toString())
            .redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            assertThat(process.waitFor(60, TimeUnit.SECONDS)).isTrue();
            assertThat(process.exitValue()).withFailMessage(Files.readString(log)).isZero();
            assertThat(Files.readString(output)).contains("\"request_count\": 22", "\"model_evaluated\": false");
        } finally {
            if (process.isAlive()) process.destroyForcibly();
        }
    }
}
