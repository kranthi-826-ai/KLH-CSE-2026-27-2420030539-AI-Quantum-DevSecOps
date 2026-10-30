package com.pqc.security.business.service;

import com.pqc.security.audit.SecurityEventOutbox;
import com.pqc.security.business.client.AdaptivePolicyClient;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.dto.PolicyDecision;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;
import static com.pqc.security.crypto.api.CryptoProfiles.CLASSICAL;

@SpringBootTest(properties={"monitoring.outbox.dispatch-enabled=false",
        "spring.datasource.url=jdbc:h2:mem:post_crypto_audit;MODE=MySQL;DB_CLOSE_DELAY=-1"})
class PostCryptoAuditFailureTests {
    @Autowired AdaptiveSecurityService service;
    @Autowired CryptoExecutionRepository repository;
    @Autowired JdbcTemplate jdbc;
    @Autowired MeterRegistry meters;
    @MockitoBean AdaptivePolicyClient client;
    @MockitoSpyBean SecurityEventOutbox outbox;

    AdaptiveSecureRequest request(String correlation) {
        when(client.evaluate(any(),eq(correlation))).thenReturn(new PolicyDecision("decision-1","LOW","LOW",.2,
                "synthetic model risk","CLASSICAL",CLASSICAL,"low risk fixture","1.1.0","model",correlation));
        return new AdaptiveSecureRequest("synthetic plaintext",Map.of("dur",.1),"INTERNAL",true,true,100);
    }

    double failedCount() {
        var counter=meters.find("adaptive_security_executions_total")
                .tags("outcome","failed","mode","CLASSICAL","risk","LOW").counter();
        return counter==null ? 0 : counter.count();
    }

    @Test void rolledBackSuccessCommitsFailedFlowWithoutErasingActualCryptoVerification() {
        String correlation="post-crypto-"+UUID.randomUUID();
        var body=request(correlation);
        var failure=new IllegalStateException("SYNTHETIC completion enqueue failure");
        double failuresBefore=failedCount();
        doThrow(failure).doCallRealMethod().when(outbox).enqueue(any());
        try {
            assertThatThrownBy(()->service.protect(body,"fixture",correlation)).isSameAs(failure);
            var rows=repository.findTop100ByOrderByExecutedAtDesc().stream()
                    .filter(row->correlation.equals(row.getCorrelationId())).toList();
            assertThat(rows).hasSize(1);
            var row=rows.getFirst();
            assertThat(row.getOutcome()).isEqualTo("FAILED");
            assertThat(row.isRoundTripVerified()).isTrue();
            assertThat(row.getDecisionId()).isEqualTo("decision-1");
            assertThat(row.getSelectedMode()).isEqualTo("CLASSICAL");
            assertThat(row.getErrorDetail()).isEqualTo("Adaptive security operation failed");
            assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE correlation_id=? AND status='PENDING'",
                    Long.class,correlation)).isEqualTo(1);
            assertThat(jdbc.queryForObject("SELECT outcome FROM audit_outbox WHERE correlation_id=?",String.class,correlation)).isEqualTo("FAILURE");
            assertThat(jdbc.queryForObject("SELECT event_type FROM audit_outbox WHERE correlation_id=?",String.class,correlation)).isEqualTo("API_ACCESS_DENIED");
            assertThat(failedCount()).isEqualTo(failuresBefore+1);
            assertThat(meters.find("adaptive_security_executions_total").tag("outcome","success").counter()).isNull();
        } finally {doCallRealMethod().when(outbox).enqueue(any());}
    }

    @Test void persistentFailureKeepsOriginalCauseNoFalseSuccessAndSignalsUnrecordedFailure() {
        String correlation="lost-audit-"+UUID.randomUUID();
        var body=request(correlation);
        var original=new IllegalStateException("SYNTHETIC first storage failure");
        var secondary=new IllegalArgumentException("SYNTHETIC second storage failure");
        double failuresBefore=failedCount();
        double before=meters.find("adaptive_security_failure_audit_errors_total").counter()==null ? 0
                : meters.get("adaptive_security_failure_audit_errors_total").counter().count();
        doThrow(original).doThrow(secondary).when(outbox).enqueue(any());
        try {
            assertThatThrownBy(()->service.protect(body,"fixture",correlation)).isSameAs(original);
            assertThat(original.getSuppressed()).containsExactly(secondary);
            var row=repository.findTop100ByOrderByExecutedAtDesc().stream()
                    .filter(value->correlation.equals(value.getCorrelationId())).findFirst().orElseThrow();
            assertThat(row.getOutcome()).isEqualTo("STARTED"); // Completion and failure transactions both rolled back.
            assertThat(row.isRoundTripVerified()).isFalse(); // Stored state has no durable crypto result.
            assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE correlation_id=?",Long.class,correlation)).isZero();
            assertThat(meters.get("adaptive_security_failure_audit_errors_total").counter().count()).isEqualTo(before+1);
            assertThat(failedCount()).isEqualTo(failuresBefore+1);
            assertThat(meters.find("adaptive_security_executions_total").tag("outcome","success").counter()).isNull();
        } finally {doCallRealMethod().when(outbox).enqueue(any());}
    }
}
