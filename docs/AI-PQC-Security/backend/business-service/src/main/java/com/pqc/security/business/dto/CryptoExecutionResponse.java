package com.pqc.security.business.dto;

import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.security.PublicFailureMessages;
import java.time.Instant;

public record CryptoExecutionResponse(
        String executionId, Instant executedAt, String decisionId, String correlationId,
        String username, String riskLevel, double riskScore, String selectedMode,
        String algorithmProfile, String selectionReason, String policyVersion, String modelVersion,
        long policyLatencyMillis, long cryptoLatencyMillis, long totalLatencyMillis,
        boolean roundTripVerified, String outcome, String errorDetail) {
    public static CryptoExecutionResponse from(CryptoExecutionEntity entity) {
        return new CryptoExecutionResponse(entity.getExecutionId(), entity.getExecutedAt(),
                entity.getDecisionId(), entity.getCorrelationId(), entity.getUsername(),
                entity.getRiskLevel(), entity.getRiskScore(), entity.getSelectedMode(),
                entity.getAlgorithmProfile(), entity.getSelectionReason(), entity.getPolicyVersion(), entity.getModelVersion(),
                entity.getPolicyLatencyMillis(), entity.getCryptoLatencyMillis(),
                entity.getTotalLatencyMillis(), entity.isRoundTripVerified(),
                entity.getOutcome(), PublicFailureMessages.forStoredDetail(entity.getErrorDetail()));
    }
}
