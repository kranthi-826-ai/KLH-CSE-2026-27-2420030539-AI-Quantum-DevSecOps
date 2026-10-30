package com.pqc.security.monitoring.repository;

import java.net.URI;
import java.net.http.*;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class EventIdempotencyHttpTests {
    @Value("${local.server.port}") int port;
    @Value("${monitoring.api-key}") String key;
    @Autowired SecurityEventRepository events;
    int send(String body) throws Exception {
        return HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/events/internal"))
                .header("Content-Type", "application/json").header("X-Internal-API-Key", key)
                .POST(HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.discarding()).statusCode();
    }
    @Test void realHttpRetryAndConflictingIdentityHaveDistinctStatuses() throws Exception {
        var id = UUID.randomUUID();
        String body = "{\"eventId\":\"" + id + "\",\"occurredAt\":\"2026-10-20T10:00:00.123456789Z\",\"eventType\":\"LOGIN_FAILED\",\"outcome\":\"FAILURE\",\"sourceService\":\"auth-service\",\"detail\":\"original\"}";
        assertThat(send(body)).isEqualTo(201);
        assertThat(send(body)).isEqualTo(200);
        assertThat(send(body.replace("original", "modified"))).isEqualTo(409);
        assertThat(events.findByEventId(id.toString()).orElseThrow().getDetail()).isEqualTo("original");
    }
}
