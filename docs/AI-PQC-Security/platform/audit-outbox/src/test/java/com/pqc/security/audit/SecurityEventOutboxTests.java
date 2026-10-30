package com.pqc.security.audit;

import com.pqc.security.events.*;
import java.time.*;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.support.JdbcTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import static org.assertj.core.api.Assertions.*;

class SecurityEventOutboxTests {
    JdbcTemplate jdbc;
    JdbcTransactionManager manager;
    MutableClock clock;
    SecurityEventOutbox store;

    @BeforeEach void setup() {
        var source = new DriverManagerDataSource("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        manager = new JdbcTransactionManager(source);
        clock = new MutableClock();
        store = new SecurityEventOutbox(jdbc, manager, clock, 2);
    }

    SecurityEvent event() {
        return SecurityEvent.create(SecurityEventType.LOGIN_SUCCEEDED, SecurityOutcome.SUCCESS,
                "auth-service", "test-user", "correlation", "POST", "/api/v1/auth/login", "127.0.0.1", "Test audit");
    }

    @Test void eventSurvivesStoreReconstructionAndPreservesItsIdentityAndTimestamp() {
        var event = event();
        store.enqueue(event);
        var reconstructed = new SecurityEventOutbox(jdbc, manager, clock, 2);
        assertThat(reconstructed.count("PENDING")).isEqualTo(1);
        assertThat(reconstructed.dispatchOne(received -> assertThat(received).isEqualTo(event))).isTrue();
        assertThat(reconstructed.count("DELIVERED")).isEqualTo(1);
        assertThat(reconstructed.dispatchOne(received -> fail("Already acknowledged"))).isFalse();
    }

    @Test void outageRetainsEventAndBackoffPreventsImmediateRetry() {
        store.enqueue(event());
        assertThat(store.dispatchOne(event -> {throw new IllegalStateException("secret-must-not-be-stored");})).isTrue();
        assertThat(store.count("PENDING")).isEqualTo(1);
        assertThat(jdbc.queryForObject("SELECT last_error_code FROM audit_outbox", String.class)).isEqualTo("DELIVERY_UNAVAILABLE");
        assertThat(store.dispatchOne(event -> fail("Retry is not due"))).isFalse();
        clock.now += 2000;
        assertThat(store.dispatchOne(event -> {})).isTrue();
        assertThat(store.count("DELIVERED")).isEqualTo(1);
    }

    @Test void exhaustedAndPermanentFailuresAreRetainedAsDeadNotDeleted() {
        store.enqueue(event());
        store.dispatchOne(event -> {throw new IllegalStateException();});
        clock.now += 2000;
        store.dispatchOne(event -> {throw new IllegalStateException();});
        assertThat(store.count("DEAD")).isEqualTo(1);
        store.enqueue(event());
        store.dispatchOne(event -> {throw new SecurityEventOutbox.PermanentDeliveryFailure();});
        assertThat(store.count("DEAD")).isEqualTo(2);
        assertThat(store.count("PENDING")).isZero();
    }

    @Test void surroundingTransactionRollsBackTheEvent() {
        assertThatThrownBy(() -> new TransactionTemplate(manager).execute(ignored -> {
            store.enqueue(event());
            throw new IllegalStateException("rollback business write");
        })).isInstanceOf(IllegalStateException.class);
        assertThat(store.count("PENDING")).isZero();
    }

    @Test void concurrentWorkersCannotDeliverTheSameLockedRow() throws Exception {
        store.enqueue(event());
        var entered = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        var delivered = new AtomicInteger();
        try (var pool = Executors.newFixedThreadPool(2)) {
            var first = pool.submit(() -> store.dispatchOne(event -> {
                delivered.incrementAndGet(); entered.countDown();
                try { if (!release.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("test deadline"); }
                catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IllegalStateException(error); }
            }));
            assertThat(entered.await(5, TimeUnit.SECONDS)).isTrue();
            var second = pool.submit(() -> store.dispatchOne(event -> delivered.incrementAndGet()));
            try { assertThat(second.get(2, TimeUnit.SECONDS)).isFalse(); }
            finally { release.countDown(); }
            assertThat(first.get(5, TimeUnit.SECONDS)).isTrue();
        }
        assertThat(delivered).hasValue(1);
    }

    static class MutableClock extends Clock {
        long now = 1700000000000L;
        public ZoneId getZone() {return ZoneOffset.UTC;}
        public Clock withZone(ZoneId zone) {return this;}
        public Instant instant() {return Instant.ofEpochMilli(now);}
        public long millis() {return now;}
    }
}
