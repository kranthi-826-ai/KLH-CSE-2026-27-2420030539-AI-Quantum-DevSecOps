package com.pqc.security.policy.service;

import com.pqc.security.policy.domain.CryptoMode;
import com.pqc.security.policy.domain.RiskLevel;

public record PolicySelection(
        RiskLevel effectiveRiskLevel,
        CryptoMode mode,
        String algorithmProfile,
        String reason) {
}
