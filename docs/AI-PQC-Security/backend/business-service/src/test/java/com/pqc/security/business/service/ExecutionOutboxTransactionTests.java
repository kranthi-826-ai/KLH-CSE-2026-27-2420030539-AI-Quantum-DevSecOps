package com.pqc.security.business.service;

import com.pqc.security.audit.SecurityEventOutbox;
import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@SpringBootTest(properties = {"monitoring.outbox.dispatch-enabled=false",
        "spring.datasource.url=jdbc:h2:mem:execution_outbox;MODE=MySQL;DB_CLOSE_DELAY=-1"})
class ExecutionOutboxTransactionTests {
    @Autowired ExecutionAuditWriter writer;
    @Autowired CryptoExecutionRepository repository;
    @Autowired JdbcTemplate jdbc;
    @MockitoSpyBean SecurityEventOutbox outbox;

    CryptoExecutionEntity completed() {
        var id = UUID.randomUUID().toString();
        var row = new CryptoExecutionEntity(id, Instant.now(), id, "test-user", "test-payload-hash");
        row.complete("decision", "LOW", .1, "CLASSICAL", "profile", "reason", "policy", "model", 1, 2, 3, true);
        return row;
    }

    @Test void completedExecutionAndPendingEventCommitTogether() {
        var row = completed();
        writer.save(row, "127.0.0.1");
        assertThat(repository.findById(row.getExecutionId())).isPresent();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE correlation_id=? AND status='PENDING'", Long.class, row.getCorrelationId())).isEqualTo(1);
    }

    @Test void queueFailureCannotLeaveSuccessfulExecutionWithoutItsEvent() {
        var row = completed();
        doThrow(new IllegalStateException("test-only queue failure")).when(outbox).enqueue(any());
        try {
            assertThatThrownBy(() -> writer.save(row, "127.0.0.1")).isInstanceOf(IllegalStateException.class);
            assertThat(repository.findById(row.getExecutionId())).isEmpty();
        } finally { doCallRealMethod().when(outbox).enqueue(any()); }
    }
}
