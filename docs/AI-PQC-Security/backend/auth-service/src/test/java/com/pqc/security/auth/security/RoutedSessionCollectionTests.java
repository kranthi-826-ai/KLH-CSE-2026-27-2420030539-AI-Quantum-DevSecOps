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

@EnabledIfSystemProperty(named = "routed.collector.python", matches = ".+")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
    "spring.datasource.url=jdbc:h2:mem:routed_lab;MODE=MySQL;DB_CLOSE_DELAY=-1",
    "spring.datasource.driver-class-name=org.h2.Driver", "spring.datasource.username=sa",
    "spring.datasource.password=", "spring.jpa.hibernate.ddl-auto=create-drop", "eureka.client.enabled=false"})
class RoutedSessionCollectionTests {
    @Value("${local.server.port}") private int port;
    @Value("${spring.datasource.url}") private String datasource;
    @MockitoBean private SecurityEventPublisher eventPublisher;
    @Test void routeRealGatewayRequestsToRealAuthenticationService() throws Exception {
        assertThat(datasource).startsWith("jdbc:h2:mem:routed_lab");
        Path root = Path.of(System.getProperty("routed.collector.root")).toAbsolutePath();
        Path output = Path.of(System.getProperty("routed.collector.output")).toAbsolutePath();
        assertThat(Files.exists(output)).isFalse();
        Files.createDirectories(output);
        var arguments = new java.util.ArrayList<>(java.util.List.of(System.getProperty("routed.collector.pwsh"), "-NoProfile", "-File",
            root.resolve("scripts/run-routed-gateway-child.ps1").toString(), "-AuthUrl", "http://127.0.0.1:" + port,
            "-OutputRoot", output.toString(), "-PythonPath", System.getProperty("routed.collector.python")));
        boolean controlsOnly = Boolean.getBoolean("routed.controls-only");
        if (controlsOnly) arguments.add("-ControlsOnly");
        if (Boolean.getBoolean("routed.rich")) arguments.add("-Rich");
        var process = new ProcessBuilder(arguments)
            .redirectErrorStream(true).redirectOutput(output.resolve("gateway-child.log").toFile()).start();
        try {
            assertThat(process.waitFor(420, TimeUnit.SECONDS)).isTrue();
            assertThat(process.exitValue()).withFailMessage(Files.readString(output.resolve("gateway-child.log"))).isZero();
            assertThat(Files.exists(output.resolve(controlsOnly ? "controls.json" : "raw/manifest.json"))).isTrue();
        } finally {
            if (process.isAlive()) {
                process.descendants().forEach(child -> child.destroyForcibly());
                process.destroyForcibly();
            }
        }
    }
}
