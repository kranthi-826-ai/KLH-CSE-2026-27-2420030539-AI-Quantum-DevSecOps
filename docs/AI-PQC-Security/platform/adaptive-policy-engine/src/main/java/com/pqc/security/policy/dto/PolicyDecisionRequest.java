package com.pqc.security.policy.dto;

import com.pqc.security.policy.domain.DataSensitivity;
import com.pqc.security.policy.domain.RiskLevel;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

public record PolicyDecisionRequest(
        @NotNull RiskLevel riskLevel,
        @DecimalMin("0.0") @DecimalMax("1.0") double riskScore,
        @NotNull DataSensitivity dataSensitivity,
        boolean hybridSupported,
        boolean pqcSupported,
        @PositiveOrZero long maxCryptoLatencyMillis,
        @NotBlank String sourceService,
        String correlationId,
        String modelVersion,
        String riskExplanation) {
}
