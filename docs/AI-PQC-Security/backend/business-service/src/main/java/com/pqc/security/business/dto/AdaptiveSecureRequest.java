package com.pqc.security.business.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.util.Map;

public record AdaptiveSecureRequest(
        @NotBlank @Size(max = 65536) String data,
        @NotEmpty @Size(max = 100) Map<String, Object> networkFeatures,
        @NotBlank @Pattern(regexp = "(?i)PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED") String dataSensitivity,
        boolean hybridSupported,
        boolean pqcSupported,
        @PositiveOrZero long maxCryptoLatencyMillis) {
}
