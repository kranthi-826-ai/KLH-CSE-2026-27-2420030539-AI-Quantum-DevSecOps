package com.pqc.security.gateway.filter;

import com.pqc.security.gateway.ApiGatewayApplication;
import com.pqc.security.http.RequestBoundaryFilter;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.function.*;
import java.io.ByteArrayInputStream;
import java.net.URI;
import java.net.http.*;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(classes = {ApiGatewayApplication.class, RequestBoundaryHttpTests.Probe.class},
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false"})
class RequestBoundaryHttpTests {
    @Value("${local.server.port}") int port;
    @org.springframework.beans.factory.annotation.Autowired AtomicInteger inputCalls;

    HttpRequest.Builder request() {
        return HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/input-probe"));
    }
    HttpResponse<String> send(HttpRequest request) throws Exception {
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
    }

    @Test void actualHttpFixedAndChunkedOversizeRequestsDoNotReachHandler() throws Exception {
        int before = inputCalls.get();
        byte[] oversized = new byte[RequestBoundaryFilter.MAX_BODY_BYTES + 1];
        assertThat(send(request().POST(HttpRequest.BodyPublishers.ofByteArray(oversized)).build()).statusCode()).isEqualTo(413);
        assertThat(send(request().POST(HttpRequest.BodyPublishers.ofInputStream(
                () -> new ByteArrayInputStream(oversized))).build()).statusCode()).isEqualTo(413);
        assertThat(inputCalls.get()).isEqualTo(before);
    }

    @Test void rejectsUnsafeAndDuplicateIdsAndPreservesNormalBody() throws Exception {
        int before = inputCalls.get();
        for (var request : new HttpRequest[]{
                request().header("X-Correlation-ID", "x".repeat(81)).POST(HttpRequest.BodyPublishers.ofString("ignored")).build(),
                request().header("X-Correlation-ID", "one").header("X-Correlation-ID", "two")
                        .POST(HttpRequest.BodyPublishers.ofString("ignored")).build()}) {
            var result = send(request);
            assertThat(result.statusCode()).isEqualTo(400);
            assertThat(result.headers().firstValue("X-Correlation-ID").orElseThrow()).hasSize(36);
            assertThat(result.headers().firstValue("Cache-Control")).contains("no-store");
        }
        assertThat(inputCalls.get()).isEqualTo(before);
        var valid = send(request().header("X-Correlation-ID", "valid-" + "a".repeat(74))
                .header("Content-Type", "text/plain").POST(HttpRequest.BodyPublishers.ofString("body survived")).build());
        assertThat(valid.statusCode()).isEqualTo(200);
        assertThat(valid.body()).contains("body survived");
        assertThat(valid.headers().firstValue("X-Correlation-ID").orElseThrow()).hasSize(80);
        assertThat(inputCalls.get()).isEqualTo(before + 1);
    }

    @TestConfiguration
    static class Probe {
        @Bean AtomicInteger inputCalls() { return new AtomicInteger(); }
        @Bean RouterFunction<ServerResponse> inputProbe(AtomicInteger calls) {
            return RouterFunctions.route().POST("/api/v1/input-probe", request -> {
                calls.incrementAndGet();
                return ServerResponse.ok().body(Map.of("body", request.body(String.class)));
            }).build();
        }
    }
}
