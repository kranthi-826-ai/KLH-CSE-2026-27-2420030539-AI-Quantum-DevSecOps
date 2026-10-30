package com.pqc.security.policy.service;

import com.pqc.security.policy.domain.CryptoMode;
import com.pqc.security.policy.domain.DataSensitivity;
import com.pqc.security.policy.domain.RiskLevel;
import com.pqc.security.policy.dto.PolicyDecisionRequest;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class PolicyRulesTests {

    private final PolicyRules rules = new PolicyRules();

    @Test
    void lowRiskSelectsClassical() {
        PolicySelection result = rules.select(request(RiskLevel.LOW, DataSensitivity.INTERNAL, true, true, 100));
        assertThat(result.mode()).isEqualTo(CryptoMode.CLASSICAL);
    }

    @Test
    void mediumRiskSelectsHybrid() {
        PolicySelection result = rules.select(request(RiskLevel.MEDIUM, DataSensitivity.INTERNAL, true, true, 100));
        assertThat(result.mode()).isEqualTo(CryptoMode.HYBRID);
    }

    @Test
    void highRiskSelectsPqc() {
        PolicySelection result = rules.select(request(RiskLevel.HIGH, DataSensitivity.INTERNAL, true, true, 100));
        assertThat(result.mode()).isEqualTo(CryptoMode.PQC);
    }

    @Test
    void confidentialDataElevatesLowRiskToMedium() {
        PolicySelection result = rules.select(request(RiskLevel.LOW, DataSensitivity.CONFIDENTIAL, true, true, 100));
        assertThat(result.effectiveRiskLevel()).isEqualTo(RiskLevel.MEDIUM);
        assertThat(result.mode()).isEqualTo(CryptoMode.HYBRID);
    }

    @Test
    void restrictedDataRequiresHighRiskPolicy() {
        PolicySelection result = rules.select(request(RiskLevel.LOW, DataSensitivity.RESTRICTED, true, true, 100));
        assertThat(result.effectiveRiskLevel()).isEqualTo(RiskLevel.HIGH);
        assertThat(result.mode()).isEqualTo(CryptoMode.PQC);
    }

    @Test
    void incompatiblePqcFallsBackAndExplainsReason() {
        PolicySelection result = rules.select(request(RiskLevel.HIGH, DataSensitivity.INTERNAL, true, false, 100));
        assertThat(result.mode()).isEqualTo(CryptoMode.HYBRID);
        assertThat(result.reason()).contains("fallback");
    }

    @Test
    void insufficientLatencyBudgetFallsBackToClassical() {
        PolicySelection result = rules.select(request(RiskLevel.HIGH, DataSensitivity.INTERNAL, true, true, 5));
        assertThat(result.mode()).isEqualTo(CryptoMode.CLASSICAL);
        assertThat(result.reason()).contains("fallback");
    }

    private PolicyDecisionRequest request(
            RiskLevel risk,
            DataSensitivity sensitivity,
            boolean hybrid,
            boolean pqc,
            long latency) {
        return new PolicyDecisionRequest(
                risk, 0.8, sensitivity, hybrid, pqc, latency,
                "test-service", "test-correlation", "test-model", "test-risk");
    }
}
