package com.pqc.security.policy.dto;

import com.pqc.security.policy.domain.CryptoMode;
import com.pqc.security.policy.domain.DataSensitivity;
import com.pqc.security.policy.domain.RiskLevel;
import com.pqc.security.policy.entity.PolicyDecisionEntity;

import java.time.Instant;

public record PolicyDecisionResponse(
        String decisionId,
        Instant decidedAt,
        RiskLevel inputRiskLevel,
        RiskLevel effectiveRiskLevel,
        double riskScore,
        DataSensitivity dataSensitivity,
        boolean hybridSupported,
        boolean pqcSupported,
        long maxCryptoLatencyMillis,
        String riskExplanation,
        CryptoMode selectedMode,
        String algorithmProfile,
        String reason,
        String policyVersion,
        String modelVersion,
        String sourceService,
        String correlationId) {

    public static PolicyDecisionResponse from(PolicyDecisionEntity entity) {
        return new PolicyDecisionResponse(
                entity.getDecisionId(), entity.getDecidedAt(),
                RiskLevel.valueOf(entity.getInputRiskLevel()),
                RiskLevel.valueOf(entity.getEffectiveRiskLevel()),
                entity.getRiskScore(), DataSensitivity.valueOf(entity.getDataSensitivity()),
                entity.isHybridSupported(), entity.isPqcSupported(),
                entity.getMaxCryptoLatencyMillis(), entity.getRiskExplanation(),
                CryptoMode.valueOf(entity.getSelectedMode()),
                entity.getAlgorithmProfile(), entity.getReason(), entity.getPolicyVersion(),
                entity.getModelVersion(), entity.getSourceService(), entity.getCorrelationId());
    }
}
