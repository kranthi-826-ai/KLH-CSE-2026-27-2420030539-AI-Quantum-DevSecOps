package com.pqc.security.policy.dto;

import com.pqc.security.policy.domain.DataSensitivity;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

import java.util.Map;

public record NetworkPolicyRequest(
        @NotEmpty Map<String, Object> features,
        @NotNull DataSensitivity dataSensitivity,
        boolean hybridSupported,
        boolean pqcSupported,
        @PositiveOrZero long maxCryptoLatencyMillis,
        @NotBlank String sourceService,
        String correlationId) {
}
