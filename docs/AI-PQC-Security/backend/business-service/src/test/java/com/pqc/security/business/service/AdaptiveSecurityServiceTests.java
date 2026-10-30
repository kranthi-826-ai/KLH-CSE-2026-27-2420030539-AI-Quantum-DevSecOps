package com.pqc.security.business.service;

import com.pqc.security.business.client.AdaptivePolicyClient;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.dto.PolicyDecision;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import org.junit.jupiter.api.Test;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

import java.util.Map;

import static com.pqc.security.crypto.api.CryptoProfiles.HYBRID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static com.pqc.security.crypto.api.CryptoProfiles.CLASSICAL;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.ArgumentCaptor;
import com.pqc.security.business.entity.CryptoExecutionEntity;

class AdaptiveSecurityServiceTests {
    @org.junit.jupiter.params.ParameterizedTest
    @org.junit.jupiter.params.provider.ValueSource(strings = {"", "\"riskScore\":null,"})
    void omittedOrNullPolicyScoreSurvivesHttpDecodingAsMissingAndIsDenied(String scoreField) throws Exception {
        var server = com.sun.net.httpserver.HttpServer.create(new java.net.InetSocketAddress("127.0.0.1", 0), 0);
        String json = "{\"decisionId\":\"http-fixture\",\"inputRiskLevel\":\"LOW\",\"effectiveRiskLevel\":\"LOW\","
                + scoreField + "\"selectedMode\":\"CLASSICAL\",\"algorithmProfile\":\"" + CLASSICAL
                + "\",\"reason\":\"fixture\",\"policyVersion\":\"1.1.0\",\"modelVersion\":\"model\","
                + "\"correlationId\":\"correlation-1\"}";
        server.createContext("/api/v1/policies/decisions/evaluate-network", exchange -> {
            exchange.getRequestBody().readAllBytes();
            byte[] bytes = json.getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, bytes.length);
            try (var output = exchange.getResponseBody()) { output.write(bytes); }
            finally { exchange.close(); }
        });
        server.start();
        try {
            var repository = mock(CryptoExecutionRepository.class);
            var client = new AdaptivePolicyClient("http://127.0.0.1:" + server.getAddress().getPort(), "synthetic-key");
            assertThatThrownBy(() -> service(client, repository, new SimpleMeterRegistry())
                    .protect(request(), "researcher", "correlation-1"))
                    .isInstanceOf(java.security.GeneralSecurityException.class).hasMessageContaining("risk score");
            var audits = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
            verify(repository, org.mockito.Mockito.times(2)).save(audits.capture());
            assertThat(audits.getValue().getOutcome()).isEqualTo("FAILED");
            assertThat(audits.getValue().getDecisionId()).isNull();
            assertThat(audits.getValue().getCryptoLatencyMillis()).isZero();
        } finally { server.stop(0); }
    }

    @org.junit.jupiter.params.ParameterizedTest
    @org.junit.jupiter.params.provider.ValueSource(strings = {"missing-score", "input-risk", "sensitivity",
            "hybrid-unsupported", "pqc-unsupported", "policy-version", "missing-model", "missing-reason"})
    void malformedDecisionFailsBeforeCryptoAndRetainsFailedAudit(String defect) {
        var client = mock(AdaptivePolicyClient.class);
        var repository = mock(CryptoExecutionRepository.class);
        boolean hybrid = !defect.equals("hybrid-unsupported");
        boolean pqc = !defect.equals("pqc-unsupported");
        String mode = defect.equals("hybrid-unsupported") ? "HYBRID"
                : defect.equals("pqc-unsupported") ? "PQC" : "CLASSICAL";
        String profile = mode.equals("HYBRID") ? HYBRID : mode.equals("PQC")
                ? com.pqc.security.crypto.api.CryptoProfiles.PQC : CLASSICAL;
        var request = new AdaptiveSecureRequest("payload", Map.of("dur", .1),
                defect.equals("sensitivity") ? "RESTRICTED" : "INTERNAL", hybrid, pqc, 100);
        when(client.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "invalid-decision", defect.equals("input-risk") ? "HIGH" : "LOW", "LOW",
                defect.equals("missing-score") ? null : .2, "risk", mode, profile,
                defect.equals("missing-reason") ? null : "selection",
                defect.equals("policy-version") ? "unknown" : "1.1.0",
                defect.equals("missing-model") ? null : "model", "correlation-1"));
        assertThatThrownBy(() -> service(client, repository, new SimpleMeterRegistry())
                .protect(request, "researcher", "correlation-1"))
                .isInstanceOf(java.security.GeneralSecurityException.class);
        var audits = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository, org.mockito.Mockito.times(2)).save(audits.capture());
        var failed = audits.getValue();
        assertThat(failed.getOutcome()).isEqualTo("FAILED");
        assertThat(failed.getDecisionId()).isNull();
        assertThat(failed.getSelectedMode()).isNull();
        assertThat(failed.getCryptoLatencyMillis()).isZero();
        assertThat(failed.isRoundTripVerified()).isFalse();
    }

    private AdaptiveSecurityService service(AdaptivePolicyClient client, CryptoExecutionRepository repository, SimpleMeterRegistry meters) {
        return new AdaptiveSecurityService(client, new ExecutionAuditWriter(repository,
                mock(com.pqc.security.business.event.SecurityEventPublisher.class)), meters);
    }

    @Test
    void rejectsHighRiskClassicalDowngradeAndPreservesDecisionEvidence() {
        AdaptivePolicyClient client = mock(AdaptivePolicyClient.class);
        CryptoExecutionRepository repository = mock(CryptoExecutionRepository.class);
        when(client.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "downgrade", "HIGH", "HIGH", .9, "risk", "CLASSICAL", CLASSICAL,
                "latency fallback", "1.1.0", "model", "correlation-1"));
        var service = service(client, repository, new SimpleMeterRegistry());
        assertThatThrownBy(() -> service.protect(request(), "researcher", "correlation-1"))
                .isInstanceOf(java.security.GeneralSecurityException.class)
                .hasMessageContaining("High-risk operation denied");
        ArgumentCaptor<CryptoExecutionEntity> audit = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository, org.mockito.Mockito.times(2)).save(audit.capture());
        var failed = audit.getValue();
        assertThat(failed.getOutcome()).isEqualTo("FAILED");
        assertThat(failed.getDecisionId()).isEqualTo("downgrade");
        assertThat(failed.getSelectedMode()).isEqualTo("CLASSICAL");
        assertThat(failed.isRoundTripVerified()).isFalse();
    }

    @Test
    void rejectsPolicyModeAndProfileMismatch() {
        AdaptivePolicyClient client = mock(AdaptivePolicyClient.class);
        CryptoExecutionRepository repository = mock(CryptoExecutionRepository.class);
        when(client.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "mismatch", "LOW", "LOW", .2, "risk", "HYBRID", CLASSICAL,
                "invalid", "1.1.0", "model", "correlation-1"));
        var service = service(client, repository, new SimpleMeterRegistry());
        assertThatThrownBy(() -> service.protect(request(), "researcher", "correlation-1"))
                .isInstanceOf(java.security.GeneralSecurityException.class)
                .hasMessageContaining("profile disagree");
    }

    @Test
    void rejectsMismatchedCorrelation() {
        AdaptivePolicyClient client = mock(AdaptivePolicyClient.class);
        when(client.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "wrong-request", "LOW", "LOW", .2, "risk", "CLASSICAL", CLASSICAL,
                "selection", "1.1.0", "model", "other-request"));
        var service = service(client, mock(CryptoExecutionRepository.class), new SimpleMeterRegistry());
        assertThatThrownBy(() -> service.protect(request(), "researcher", "correlation-1"))
                .isInstanceOf(java.security.GeneralSecurityException.class)
                .hasMessageContaining("correlation mismatch");
    }

    @Test
    void dependencyFailureCannotProduceSuccessfulProtection() {
        AdaptivePolicyClient client = mock(AdaptivePolicyClient.class);
        CryptoExecutionRepository repository = mock(CryptoExecutionRepository.class);
        when(client.evaluate(any(), anyString())).thenThrow(new IllegalStateException("Unavailable"));
        var service = service(client, repository, new SimpleMeterRegistry());
        assertThatThrownBy(() -> service.protect(request(), "researcher", "correlation-1"))
                .isInstanceOf(IllegalStateException.class);
        ArgumentCaptor<CryptoExecutionEntity> audit = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository, org.mockito.Mockito.times(2)).save(audit.capture());
        assertThat(audit.getValue().getOutcome()).isEqualTo("FAILED");
    }

    private AdaptiveSecureRequest request() {
        return new AdaptiveSecureRequest("payload", Map.of("dur", .1), "INTERNAL", true, true, 100);
    }

    @Test
    void rejectsNonFiniteModelScoreBeforeRecordingInvalidDecisionData() {
        AdaptivePolicyClient client = mock(AdaptivePolicyClient.class);
        CryptoExecutionRepository repository = mock(CryptoExecutionRepository.class);
        when(client.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "invalid-score", "LOW", "LOW", Double.NaN, "risk", "CLASSICAL", CLASSICAL,
                "selection", "1.1.0", "model", "correlation-1"));
        var service = service(client, repository, new SimpleMeterRegistry());
        assertThatThrownBy(() -> service.protect(request(), "researcher", "correlation-1"))
                .isInstanceOf(java.security.GeneralSecurityException.class)
                .hasMessageContaining("risk score");
        ArgumentCaptor<CryptoExecutionEntity> audit = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository, org.mockito.Mockito.times(2)).save(audit.capture());
        assertThat(audit.getValue().getDecisionId()).isNull();
        assertThat(audit.getValue().getOutcome()).isEqualTo("FAILED");
    }

    @Test
    void appliesPolicyProfileAndVerifiesEncryptedRoundTrip() throws Exception {
        AdaptivePolicyClient policyClient = mock(AdaptivePolicyClient.class);
        CryptoExecutionRepository repository = mock(CryptoExecutionRepository.class);
        when(policyClient.evaluate(any(), anyString())).thenReturn(new PolicyDecision(
                "decision-1", "HIGH", "HIGH", 0.91, "test risk",
                "HYBRID", HYBRID, "test selection", "1.1.0", "model-1", "correlation-1"));

        SimpleMeterRegistry meters = new SimpleMeterRegistry();
        AdaptiveSecurityService service = service(policyClient, repository, meters);
        AdaptiveSecureRequest request = new AdaptiveSecureRequest(
                "classified payload", Map.of("dur", 0.1), "CONFIDENTIAL", true, true, 100);

        var response = service.protect(request, "researcher", "correlation-1");

        assertThat(response.algorithmProfile()).isEqualTo(HYBRID);
        assertThat(response.roundTripVerified()).isTrue();
        assertThat(response.encryptedPayload()).isNotBlank();
        assertThat(response.encryptedPayload()).doesNotContain("classified payload");
        verify(repository, org.mockito.Mockito.times(2)).save(any());
        ArgumentCaptor<CryptoExecutionEntity> auditCaptor = ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository, org.mockito.Mockito.times(2)).save(auditCaptor.capture());
        assertThat(auditCaptor.getAllValues().getLast().getSelectionReason()).isEqualTo("test selection");
        assertThat(meters.get("adaptive_security_executions_total").counter().count()).isEqualTo(1.0);
    }
}
