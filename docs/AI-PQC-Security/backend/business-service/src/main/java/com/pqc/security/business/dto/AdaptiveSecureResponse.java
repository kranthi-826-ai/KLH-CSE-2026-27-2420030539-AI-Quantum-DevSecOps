package com.pqc.security.business.dto;

public record AdaptiveSecureResponse(
        String executionId,
        String decisionId,
        String correlationId,
        String riskLevel,
        double riskScore,
        String selectedMode,
        String algorithmProfile,
        String policyVersion,
        String modelVersion,
        String encryptedPayload,
        String nonce,
        String encapsulation,
        String signature,
        boolean roundTripVerified,
        long policyLatencyMillis,
        long cryptoLatencyMillis,
        long totalLatencyMillis) {
}
