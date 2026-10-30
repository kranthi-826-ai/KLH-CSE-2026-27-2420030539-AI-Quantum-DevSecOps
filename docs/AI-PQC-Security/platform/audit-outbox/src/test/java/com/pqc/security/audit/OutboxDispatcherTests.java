package com.pqc.security.audit;

import com.pqc.security.events.*;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.cloud.client.DefaultServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.support.JdbcTransactionManager;
import org.springframework.web.client.RestClient;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

class OutboxDispatcherTests {
    HttpServer server;
    @AfterEach void close() {if (server != null) server.stop(0);}

    SecurityEventOutbox deliver(int status, boolean matchingId) throws Exception {
        var source = new DriverManagerDataSource("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DB_CLOSE_DELAY=-1", "sa", "");
        var outbox = new SecurityEventOutbox(new JdbcTemplate(source), new JdbcTransactionManager(source), Clock.systemUTC(), 20);
        var event = SecurityEvent.create(SecurityEventType.LOGIN_FAILED, SecurityOutcome.FAILURE,
                "auth-service", "test", "test", "POST", "/login", "127.0.0.1", "test");
        outbox.enqueue(event);
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api/v1/events/internal", exchange -> {
            assertThat(exchange.getRequestHeaders().getFirst("X-Internal-API-Key")).isEqualTo("test-only-key");
            exchange.getRequestBody().readAllBytes();
            byte[] body = ("{\"eventId\":\"" + (matchingId ? event.eventId() : UUID.randomUUID()) + "\"}").getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        server.start();
        var discovery = mock(DiscoveryClient.class);
        when(discovery.getInstances("security-monitoring-service")).thenReturn(List.of(
                new DefaultServiceInstance("monitor", "security-monitoring-service", "127.0.0.1", server.getAddress().getPort(), false)));
        new OutboxDispatcher(outbox, discovery, RestClient.create(), "test-only-key").flush();
        return outbox;
    }

    @Test void matchingCreatedReceiptAcknowledgesDelivery() throws Exception {
        assertThat(deliver(201, true).count("DELIVERED")).isEqualTo(1);
    }
    @Test void wrongReceiptIdentityDoesNotAcknowledgeDelivery() throws Exception {
        assertThat(deliver(200, false).count("PENDING")).isEqualTo(1);
    }
    @ParameterizedTest @ValueSource(ints={202,302})
    void nonDurableOrRedirectStatusDoesNotAcknowledgeDelivery(int status) throws Exception {
        assertThat(deliver(status, true).count("PENDING")).isEqualTo(1);
    }
    @Test void conflictingContentIsRetainedAsDead() throws Exception {
        assertThat(deliver(409, false).count("DEAD")).isEqualTo(1);
    }
    @Test void keyFailureIsRetryableWithinTheAttemptBudget() throws Exception {
        assertThat(deliver(401, false).count("PENDING")).isEqualTo(1);
    }
}
