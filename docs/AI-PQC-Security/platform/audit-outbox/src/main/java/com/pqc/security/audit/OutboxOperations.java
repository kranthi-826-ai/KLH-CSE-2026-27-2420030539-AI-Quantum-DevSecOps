package com.pqc.security.audit;

import java.time.Clock;
import java.util.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** Explicit single-event replay; never changes event identity, payload or occurrence time. */
public class OutboxOperations {
    private final JdbcTemplate jdbc;
    private final TransactionTemplate transactions;
    private final Clock clock;
    public static final Set<String> REASONS = Set.of("RESTORED_DEPENDENCY", "CORRECTED_CONFIGURATION", "VERIFIED_RECEIVER_STATE");

    public OutboxOperations(JdbcTemplate jdbc, PlatformTransactionManager manager, Clock clock) {
        this.jdbc = jdbc; this.transactions = new TransactionTemplate(manager); this.clock = clock;
        this.transactions.setTimeout(5);
        jdbc.execute("""
            CREATE TABLE IF NOT EXISTS audit_outbox_replay_log (
              operation_id VARCHAR(36) PRIMARY KEY, event_id VARCHAR(36) NOT NULL,
              operator_name VARCHAR(100) NOT NULL, reason VARCHAR(40) NOT NULL,
              requested_at_millis BIGINT NOT NULL, previous_attempts INT NOT NULL,
              previous_error_code VARCHAR(64)
            )
            """);
    }

    public record Preview(String eventId, String status, int attempts, String lastErrorCode) { }
    public record ReplayResult(Preview previous, boolean applied, String operationId) { }

    public java.util.List<Preview> recentDead() {
        return jdbc.query("SELECT event_id,status,attempts,last_error_code FROM audit_outbox WHERE status='DEAD' ORDER BY occurred_at_seconds DESC,event_id LIMIT 20",
                (rs, row) -> new Preview(rs.getString("event_id"), rs.getString("status"), rs.getInt("attempts"), rs.getString("last_error_code")));
    }

    public ReplayResult replay(UUID eventId, String actor, String reason, boolean apply) {
        if (eventId == null || actor == null || actor.isBlank() || actor.length() > 100 || !REASONS.contains(reason == null ? "" : reason))
            throw new IllegalArgumentException("Invalid replay request");
        return transactions.execute(ignored -> {
            var rows = jdbc.query("SELECT status,attempts,last_error_code FROM audit_outbox WHERE event_id=? FOR UPDATE",
                    (rs, row) -> new Preview(eventId.toString(), rs.getString("status"), rs.getInt("attempts"), rs.getString("last_error_code")),
                    eventId.toString());
            if (rows.isEmpty()) throw new MissingEvent();
            var previous = rows.getFirst();
            if (!previous.status().equals("DEAD")) throw new IneligibleState();
            if (!apply) return new ReplayResult(previous, false, null);
            String operationId = UUID.randomUUID().toString();
            jdbc.update("INSERT INTO audit_outbox_replay_log(operation_id,event_id,operator_name,reason,requested_at_millis,previous_attempts,previous_error_code) VALUES (?,?,?,?,?,?,?)",
                    operationId, eventId.toString(), actor, reason, clock.millis(), previous.attempts(), previous.lastErrorCode());
            jdbc.update("UPDATE audit_outbox SET status='PENDING',attempts=0,next_attempt_millis=?,delivered_at_millis=NULL,last_error_code=NULL WHERE event_id=?",
                    clock.millis(), eventId.toString());
            return new ReplayResult(previous, true, operationId);
        });
    }

    public static class MissingEvent extends RuntimeException { }
    public static class IneligibleState extends RuntimeException { }
}
