package com.pqc.security.audit;

import com.pqc.security.events.*;
import java.time.*;
import java.util.UUID;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.support.JdbcTransactionManager;
import static org.assertj.core.api.Assertions.*;

class OutboxOperationsTests {
    JdbcTemplate jdbc;
    SecurityEventOutbox store;
    OutboxOperations operations;
    SecurityEvent event;
    Clock clock = Clock.fixed(Instant.parse("2026-10-20T12:00:00Z"), ZoneOffset.UTC);
    @BeforeEach void setup() {
        var source = new DriverManagerDataSource("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        var manager = new JdbcTransactionManager(source);
        store = new SecurityEventOutbox(jdbc, manager, clock, 1);
        operations = new OutboxOperations(jdbc, manager, clock);
        event = new SecurityEvent(UUID.randomUUID(), clock.instant().minusSeconds(300), SecurityEventType.LOGIN_FAILED,
                SecurityOutcome.FAILURE, "auth-service", "test-user", "ops-test", "POST", "/login", "127.0.0.1", "test");
        store.enqueue(event);
    }
    void dead() { store.dispatchOne(value -> { throw new SecurityEventOutbox.PermanentDeliveryFailure(); }); }
    long logs() { return jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox_replay_log", Long.class); }

    @Test void dryRunDoesNotMutateAndReplayPreservesIdentityPayloadAndTime() {
        dead();
        assertThat(operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", false).applied()).isFalse();
        assertThat(store.count("DEAD")).isEqualTo(1);
        assertThat(logs()).isZero();
        var result = operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", true);
        assertThat(result.applied()).isTrue();
        assertThat(result.operationId()).isNotBlank();
        assertThat(logs()).isEqualTo(1);
        assertThat(jdbc.queryForObject("SELECT operator_name FROM audit_outbox_replay_log", String.class)).isEqualTo("operator");
        assertThatThrownBy(() -> operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", true))
                .isInstanceOf(OutboxOperations.IneligibleState.class);
        store.dispatchOne(value -> assertThat(value).isEqualTo(event));
        assertThat(store.count("DELIVERED")).isEqualTo(1);
        assertThat(logs()).isEqualTo(1);
    }

    @Test void missingPendingAndDeliveredEventsCannotBeReplayed() {
        assertThatThrownBy(() -> operations.replay(UUID.randomUUID(), "operator", "RESTORED_DEPENDENCY", true))
                .isInstanceOf(OutboxOperations.MissingEvent.class);
        assertThatThrownBy(() -> operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", false))
                .isInstanceOf(OutboxOperations.IneligibleState.class);
        store.dispatchOne(value -> {});
        assertThatThrownBy(() -> operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", true))
                .isInstanceOf(OutboxOperations.IneligibleState.class);
        assertThat(logs()).isZero();
    }

    @Test void replayLogAndStateChangeRollbackTogether() {
        dead();
        jdbc.execute("ALTER TABLE audit_outbox ADD CONSTRAINT prevent_pending CHECK(status <> 'PENDING')");
        assertThatThrownBy(() -> operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", true))
                .isInstanceOf(org.springframework.dao.DataAccessException.class);
        assertThat(logs()).isZero();
        assertThat(store.count("DEAD")).isEqualTo(1);
    }

    @Test void concurrentReplayCreatesOnlyOneOperation() throws Exception {
        dead();
        java.util.concurrent.Callable<Boolean> action = () -> {
            try { operations.replay(event.eventId(), "operator", "RESTORED_DEPENDENCY", true); return true; }
            catch (OutboxOperations.IneligibleState ignored) { return false; }
        };
        try (var pool = Executors.newFixedThreadPool(2)) {
            var first = pool.submit(action); var second = pool.submit(action);
            assertThat((first.get() ? 1 : 0) + (second.get() ? 1 : 0)).isEqualTo(1);
        }
        assertThat(logs()).isEqualTo(1);
    }

    @Test void eventAgeIsClampedAndBecomesZeroWhenNoPendingEventRemains() {
        assertThat(store.oldestPendingEventAgeSeconds()).isEqualTo(300);
        dead();
        assertThat(store.oldestPendingEventAgeSeconds()).isZero();
        var future = new SecurityEvent(UUID.randomUUID(), clock.instant().plusSeconds(60), event.eventType(), event.outcome(),
                event.sourceService(), event.username(), event.correlationId(), event.requestMethod(), event.requestPath(), event.sourceIp(), event.detail());
        store.enqueue(future);
        assertThat(store.oldestPendingEventAgeSeconds()).isZero();
    }

    @Test void invalidReasonsAndOperatorsCannotChangeState() {
        dead();
        assertThatThrownBy(() -> operations.replay(event.eventId(), "operator", "arbitrary free text", true)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> operations.replay(event.eventId(), " ", "RESTORED_DEPENDENCY", true)).isInstanceOf(IllegalArgumentException.class);
        assertThat(store.count("DEAD")).isEqualTo(1);
        assertThat(logs()).isZero();
    }
}
