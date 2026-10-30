package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class GatewayShadowSafetyTests {
    @TempDir Path directory;
    @Test void closedWriterDropsTelemetryWithoutChangingResponse() throws Exception {
        var meters = new SimpleMeterRegistry();
        var writer = new ShadowObservationWriter(directory.resolve("closed.jsonl").toString(), meters);
        writer.close();
        var filter = new GatewayShadowFilter(writer, meters, 1, 2);
        var response = new MockHttpServletResponse();
        filter.doFilter(new MockHttpServletRequest("GET", "/api/v1/auth/me"), response,
                (req, res) -> ((jakarta.servlet.http.HttpServletResponse) res).setStatus(202));
        assertThat(response.getStatus()).isEqualTo(202);
        assertThat(meters.get("gateway_shadow_dropped_total").counter().count()).isEqualTo(1.);
    }
    @Test void originalExceptionsPropagateAndAreNotMisrecordedAsSuccess() throws Exception {
        var meters = new SimpleMeterRegistry();
        var output = directory.resolve("exception.jsonl");
        try (var writer = new ShadowObservationWriter(output.toString(), meters)) {
            var filter = new GatewayShadowFilter(writer, meters, 1, 2);
            assertThatThrownBy(() -> filter.doFilter(new MockHttpServletRequest("GET", "/api/v1/auth/me"),
                new MockHttpServletResponse(), (req, res) -> { throw new ServletException("original"); }))
                .isInstanceOf(ServletException.class).hasMessage("original");
        }
        assertThat(Files.size(output)).isZero();
        assertThat(meters.get("gateway_shadow_incomplete_dropped_total").counter().count()).isEqualTo(1.);
    }
    @Test void observationCapacityDoesNotRejectNewPeers() throws Exception {
        var meters = new SimpleMeterRegistry();
        AtomicInteger forwarded = new AtomicInteger();
        try (var writer = new ShadowObservationWriter(directory.resolve("capacity.jsonl").toString(), meters)) {
            var filter = new GatewayShadowFilter(writer, meters, 1, 2);
            for (String peer : new String[]{"192.0.2.1", "192.0.2.2"}) {
                var request = new MockHttpServletRequest("GET", "/api/v1/auth/me");
                request.setRemoteAddr(peer);
                filter.doFilter(request, new MockHttpServletResponse(), (req, res) -> forwarded.incrementAndGet());
            }
        }
        assertThat(forwarded.get()).isEqualTo(2);
        assertThat(meters.get("gateway_shadow_history_capacity_dropped_total").counter().count()).isEqualTo(1.);
    }
    @Test void existingEvidenceIsNeverOverwritten() throws Exception {
        var output = directory.resolve("existing.jsonl");
        Files.writeString(output, "preserve");
        assertThatThrownBy(() -> new ShadowObservationWriter(output.toString(), new SimpleMeterRegistry()))
                .isInstanceOf(java.nio.file.FileAlreadyExistsException.class);
        assertThat(Files.readString(output)).isEqualTo("preserve");
    }
}
