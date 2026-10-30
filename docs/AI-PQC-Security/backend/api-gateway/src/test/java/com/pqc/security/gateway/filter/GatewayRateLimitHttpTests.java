package com.pqc.security.gateway.filter;

import com.pqc.security.gateway.ApiGatewayApplication;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerResponse;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(classes = {ApiGatewayApplication.class, GatewayRateLimitHttpTests.ProbeConfiguration.class},
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false",
        "security.rate-limit.api-capacity=2", "security.rate-limit.api-period-seconds=3600"})
class GatewayRateLimitHttpTests {
    @Value("${local.server.port}") private int port;
    @org.springframework.beans.factory.annotation.Autowired private AtomicInteger probeCalls;

    @Test void burstIsBlockedBeforeTheHttpHandlerAndKeepsCorrelationHeader() throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        for (int i = 0; i < 3; i++) {
            HttpRequest request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/rate-probe"))
                    .header("X-Forwarded-For", "198.51.100." + i).GET().build();
            var response = client.send(request, HttpResponse.BodyHandlers.ofString());
            assertThat(response.headers().firstValue("X-Correlation-ID")).isPresent();
            assertThat(response.statusCode()).isEqualTo(i < 2 ? 200 : 429);
            if (i == 2) {
                assertThat(response.headers().firstValue("Retry-After")).isPresent();
                assertThat(response.body()).contains("rate limit exceeded");
            }
        }
        assertThat(probeCalls.get()).isEqualTo(2);
    }

    @TestConfiguration
    static class ProbeConfiguration {
        @Bean AtomicInteger probeCalls() { return new AtomicInteger(); }
        @Bean RouterFunction<ServerResponse> rateProbe(AtomicInteger calls) {
            return RouterFunctions.route().GET("/api/v1/rate-probe", request -> {
                calls.incrementAndGet();
                return ServerResponse.ok().body(Map.of("message", "allowed"));
            }).build();
        }
    }
}
