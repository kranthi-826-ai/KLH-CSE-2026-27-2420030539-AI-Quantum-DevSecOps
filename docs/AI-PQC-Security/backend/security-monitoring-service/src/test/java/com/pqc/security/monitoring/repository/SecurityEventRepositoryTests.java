package com.pqc.security.monitoring.repository;

import com.pqc.security.events.SecurityEvent;
import com.pqc.security.events.SecurityEventType;
import com.pqc.security.events.SecurityOutcome;
import com.pqc.security.monitoring.entity.SecurityEventEntity;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class SecurityEventRepositoryTests {

    @Autowired
    private SecurityEventRepository repository;
    @Autowired private com.pqc.security.monitoring.service.SecurityEventCollector collector;

    @BeforeEach
    void clearEvents() {
        repository.deleteAll();
    }

    @Test
    void persistsNormalizedSecurityEvent() {
        SecurityEvent event = SecurityEvent.create(
                SecurityEventType.API_ACCESS_GRANTED,
                SecurityOutcome.SUCCESS,
                "business-service",
                "alice",
                "correlation-123",
                "GET",
                "/api/v1/business/secure-data",
                "127.0.0.1",
                "Protected business API accessed");

        repository.save(new SecurityEventEntity(event));

        assertThat(repository.findTop100ByOrderByOccurredAtDesc())
                .singleElement()
                .satisfies(saved -> {
                    assertThat(saved.getEventId()).isEqualTo(event.eventId().toString());
                    assertThat(saved.getEventType()).isEqualTo("API_ACCESS_GRANTED");
                    assertThat(saved.getCorrelationId()).isEqualTo("correlation-123");
                });
    }

    @Test void identicalRetryIsIdempotentButDifferentContentCannotOverwrite() {
        var event = SecurityEvent.create(SecurityEventType.LOGIN_FAILED, SecurityOutcome.FAILURE,
                "auth-service", "test", "retry", "POST", "/login", "127.0.0.1", "test");
        assertThat(collector.collect(event).created()).isTrue();
        assertThat(collector.collect(event).created()).isFalse();
        var changed = new SecurityEvent(event.eventId(), event.occurredAt(), event.eventType(), event.outcome(),
                event.sourceService(), "changed-user", event.correlationId(), event.requestMethod(), event.requestPath(), event.sourceIp(), event.detail());
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> collector.collect(changed))
                .isInstanceOf(com.pqc.security.monitoring.service.SecurityEventCollector.EventIdentityConflict.class);
        assertThat(repository.count()).isEqualTo(1);
        assertThat(repository.findByEventId(event.eventId().toString()).orElseThrow().getUsername()).isEqualTo("test");
    }

    @Test void concurrentIdenticalRetriesProduceOneStoredEvent() throws Exception {
        var event = SecurityEvent.create(SecurityEventType.LOGIN_SUCCEEDED, SecurityOutcome.SUCCESS,
                "auth-service", "test", "race", "POST", "/login", "127.0.0.1", "test");
        try (var pool = java.util.concurrent.Executors.newFixedThreadPool(4)) {
            var tasks = java.util.stream.IntStream.range(0, 8)
                    .<java.util.concurrent.Callable<Boolean>>mapToObj(i -> () -> collector.collect(event).created()).toList();
            int created = 0;
            for (var result : pool.invokeAll(tasks)) if (result.get()) created++;
            assertThat(created).isEqualTo(1);
        }
        assertThat(repository.count()).isEqualTo(1);
    }
}
