package com.pqc.security.business.service;

import com.pqc.security.business.client.AdaptivePolicyClient;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

@SpringBootTest(properties={"monitoring.outbox.dispatch-enabled=false",
        "spring.datasource.url=jdbc:h2:mem:initial_audit_failure;MODE=MySQL;DB_CLOSE_DELAY=-1"})
class InitialAuditFailureTests {
    @Autowired AdaptiveSecurityService service;
    @Autowired CryptoExecutionRepository repository;
    @Autowired JdbcTemplate jdbc;
    @Autowired MeterRegistry meters;
    @MockitoBean AdaptivePolicyClient client;
    @MockitoSpyBean ExecutionAuditWriter writer;

    double failedCount() {
        var counter=meters.find("adaptive_security_executions_total")
                .tags("outcome","failed","mode","unselected","risk","unknown").counter();
        return counter==null ? 0 : counter.count();
    }

    @ParameterizedTest
    @ValueSource(strings={"recovered","persistent","same-exception"})
    void initialSaveFailureCannotStartPolicyOrCryptoAndHasHonestAuditOutcome(String scenario) {
        String correlation="initial-fail-"+UUID.randomUUID();
        var original=new IllegalStateException("SYNTHETIC initial save failure");
        RuntimeException secondary=scenario.equals("same-exception") ? original
                : new IllegalArgumentException("SYNTHETIC fallback save failure");
        double failedBefore=failedCount();
        double lostBefore=meters.get("adaptive_security_failure_audit_errors_total").counter().count();
        if (scenario.equals("recovered")) doThrow(original).doCallRealMethod().when(writer).save(any(),any());
        else doThrow(original).doThrow(secondary).when(writer).save(any(),any());
        try {
            var request=new AdaptiveSecureRequest("synthetic payload",Map.of("dur",.1),"INTERNAL",true,true,100);
            assertThatThrownBy(()->service.protect(request,"initial-fixture",correlation)).isSameAs(original);
            verifyNoInteractions(client);
            verify(writer,times(2)).save(any(),any());
            assertThat(failedCount()).isEqualTo(failedBefore+1);
            var rows=repository.findTop100ByOrderByExecutedAtDesc().stream()
                    .filter(row->correlation.equals(row.getCorrelationId())).toList();
            if (scenario.equals("recovered")) {
                assertThat(rows).hasSize(1);
                var row=rows.getFirst();
                assertThat(row.getOutcome()).isEqualTo("FAILED");
                assertThat(row.isRoundTripVerified()).isFalse();
                assertThat(row.getDecisionId()).isNull();
                assertThat(row.getSelectedMode()).isNull();
                assertThat(row.getCryptoLatencyMillis()).isZero();
                assertThat(row.getErrorDetail()).isEqualTo("Adaptive security operation failed");
                assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE correlation_id=? AND outcome='FAILURE'",
                        Long.class,correlation)).isEqualTo(1);
                assertThat(meters.get("adaptive_security_failure_audit_errors_total").counter().count()).isEqualTo(lostBefore);
            } else {
                assertThat(rows).isEmpty();
                assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE correlation_id=?",Long.class,correlation)).isZero();
                assertThat(meters.get("adaptive_security_failure_audit_errors_total").counter().count()).isEqualTo(lostBefore+1);
                if (secondary==original) assertThat(original.getSuppressed()).isEmpty();
                else assertThat(original.getSuppressed()).containsExactly(secondary);
            }
        } finally {doCallRealMethod().when(writer).save(any(),any());}
    }
}
