package com.pqc.security.audit;

import com.pqc.security.events.SecurityEvent;
import com.pqc.security.events.SecurityEventType;
import com.pqc.security.events.SecurityOutcome;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Instant;
import java.util.UUID;
import java.util.function.Consumer;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** Durable at-least-once delivery. JDBC joins the enclosing JPA transaction. */
public class SecurityEventOutbox {
    private final JdbcTemplate jdbc;
    private final TransactionTemplate transactions;
    private final Clock clock;
    private final int maxAttempts;

    public SecurityEventOutbox(JdbcTemplate jdbc, PlatformTransactionManager manager, Clock clock, int maxAttempts) {
        if (maxAttempts < 1 || maxAttempts > 100) throw new IllegalArgumentException("Invalid retry limit");
        this.jdbc = jdbc;
        this.transactions = new TransactionTemplate(manager);
        this.clock = clock;
        this.maxAttempts = maxAttempts;
        jdbc.execute("""
            CREATE TABLE IF NOT EXISTS audit_outbox (
              event_id VARCHAR(36) PRIMARY KEY, occurred_at_seconds BIGINT NOT NULL, occurred_at_nanos INT NOT NULL,
              event_type VARCHAR(50) NOT NULL, outcome VARCHAR(20) NOT NULL,
              source_service VARCHAR(80) NOT NULL, username VARCHAR(100), correlation_id VARCHAR(80),
              request_method VARCHAR(10), request_path VARCHAR(255), source_ip VARCHAR(64), detail VARCHAR(500),
              status VARCHAR(12) NOT NULL, attempts INT NOT NULL, next_attempt_millis BIGINT NOT NULL,
              delivered_at_millis BIGINT, last_error_code VARCHAR(64)
            )
            """);
        // Both supported databases expose indexes through JDBC metadata. Avoid
        // MySQL-incompatible CREATE INDEX IF NOT EXISTS and tolerate startup races.
        try {
            jdbc.execute("CREATE INDEX ix_audit_outbox_due ON audit_outbox(status,next_attempt_millis)");
        } catch (org.springframework.dao.DataAccessException error) {
            boolean exists = Boolean.TRUE.equals(jdbc.execute((org.springframework.jdbc.core.ConnectionCallback<Boolean>) connection -> {
                var metadata = connection.getMetaData();
                String table = metadata.storesUpperCaseIdentifiers() ? "AUDIT_OUTBOX" : "audit_outbox";
                try (var indexes = metadata.getIndexInfo(connection.getCatalog(), null, table, false, false)) {
                    while (indexes.next()) if ("ix_audit_outbox_due".equalsIgnoreCase(indexes.getString("INDEX_NAME"))) return true;
                    return false;
                }
            }));
            if (!exists) throw error;
        }
    }

    public void enqueue(SecurityEvent event) {
        try {
        jdbc.update("""
            INSERT INTO audit_outbox(event_id,occurred_at_seconds,occurred_at_nanos,event_type,outcome,source_service,username,
              correlation_id,request_method,request_path,source_ip,detail,status,attempts,next_attempt_millis)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'PENDING',0,?)
            """, event.eventId().toString(), event.occurredAt().getEpochSecond(), event.occurredAt().getNano(), event.eventType().name(),
                event.outcome().name(), event.sourceService(), event.username(), event.correlationId(),
                event.requestMethod(), event.requestPath(), event.sourceIp(), event.detail(), clock.millis());
        } catch (org.springframework.dao.DataAccessException error) {
            throw new AuditUnavailableException(error);
        }
    }

    public boolean dispatchOne(Consumer<SecurityEvent> transport) {
        return Boolean.TRUE.equals(transactions.execute(ignored -> {
            var due = jdbc.query("SELECT * FROM audit_outbox WHERE status='PENDING' AND next_attempt_millis<=? ORDER BY next_attempt_millis,event_id LIMIT 1 FOR UPDATE SKIP LOCKED",
                    (rs, row) -> new Pending(readEvent(rs), rs.getInt("attempts")), clock.millis());
            if (due.isEmpty()) return false;
            var pending = due.getFirst();
            int attempts = pending.attempts() + 1;
            try {
                transport.accept(pending.event());
                jdbc.update("UPDATE audit_outbox SET status='DELIVERED',attempts=?,delivered_at_millis=?,last_error_code=NULL WHERE event_id=?",
                        attempts, clock.millis(), pending.event().eventId().toString());
            } catch (RuntimeException error) {
                // Never persist exception text, response bodies, credentials or URIs.
                boolean dead = attempts >= maxAttempts || error instanceof PermanentDeliveryFailure;
                long delay = Math.min(60_000L, 1_000L << Math.min(attempts, 6));
                jdbc.update("UPDATE audit_outbox SET status=?,attempts=?,next_attempt_millis=?,last_error_code=? WHERE event_id=?",
                        dead ? "DEAD" : "PENDING", attempts, clock.millis() + delay,
                        error instanceof PermanentDeliveryFailure ? "PERMANENT_REJECTION" : "DELIVERY_UNAVAILABLE",
                        pending.event().eventId().toString());
            }
            return true;
        }));
    }

    public long count(String status) {
        return jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE status=?", Long.class, status);
    }

    public long oldestPendingEventAgeSeconds() {
        Long oldest = jdbc.queryForObject("SELECT MIN(occurred_at_seconds) FROM audit_outbox WHERE status='PENDING'", Long.class);
        return oldest == null ? 0 : Math.max(0, clock.instant().getEpochSecond() - oldest);
    }

    private static SecurityEvent readEvent(ResultSet row) throws SQLException {
        return new SecurityEvent(UUID.fromString(row.getString("event_id")), Instant.ofEpochSecond(row.getLong("occurred_at_seconds"), row.getInt("occurred_at_nanos")),
                SecurityEventType.valueOf(row.getString("event_type")), SecurityOutcome.valueOf(row.getString("outcome")),
                row.getString("source_service"), row.getString("username"), row.getString("correlation_id"),
                row.getString("request_method"), row.getString("request_path"), row.getString("source_ip"), row.getString("detail"));
    }

    private record Pending(SecurityEvent event, int attempts) { }
    public static class PermanentDeliveryFailure extends RuntimeException { }
}
