package com.pqc.security.policy.service;

import com.pqc.security.policy.domain.CryptoMode;
import com.pqc.security.policy.domain.DataSensitivity;
import com.pqc.security.policy.domain.RiskLevel;
import com.pqc.security.policy.dto.PolicyDecisionRequest;
import org.springframework.stereotype.Component;

import static com.pqc.security.crypto.api.CryptoProfiles.CLASSICAL;
import static com.pqc.security.crypto.api.CryptoProfiles.HYBRID;
import static com.pqc.security.crypto.api.CryptoProfiles.PQC;

@Component
public class PolicyRules {

    public static final String VERSION = "1.1.0";
    static final long HYBRID_MINIMUM_MILLIS = 8;
    static final long PQC_MINIMUM_MILLIS = 15;

    public PolicySelection select(PolicyDecisionRequest request) {
        RiskLevel effectiveRisk = effectiveRisk(request.riskLevel(), request.dataSensitivity());
        if (effectiveRisk == RiskLevel.HIGH) {
            if (request.pqcSupported() && request.maxCryptoLatencyMillis() >= PQC_MINIMUM_MILLIS) {
                return selection(effectiveRisk, CryptoMode.PQC, PQC,
                        "High effective risk with PQC compatibility and sufficient latency budget");
            }
            if (request.hybridSupported() && request.maxCryptoLatencyMillis() >= HYBRID_MINIMUM_MILLIS) {
                return selection(effectiveRisk, CryptoMode.HYBRID, HYBRID,
                        "High risk required a compatibility fallback from PQC to hybrid protection");
            }
            return selection(effectiveRisk, CryptoMode.CLASSICAL, CLASSICAL,
                    "High risk required a recorded fallback because PQC and hybrid constraints were not satisfied");
        }
        if (effectiveRisk == RiskLevel.MEDIUM
                && request.hybridSupported()
                && request.maxCryptoLatencyMillis() >= HYBRID_MINIMUM_MILLIS) {
            return selection(effectiveRisk, CryptoMode.HYBRID, HYBRID,
                    "Medium effective risk selected hybrid migration protection");
        }
        return selection(effectiveRisk, CryptoMode.CLASSICAL, CLASSICAL,
                effectiveRisk == RiskLevel.LOW
                        ? "Low effective risk selected the classical profile"
                        : "Compatibility or latency constraints required the classical profile");
    }

    private RiskLevel effectiveRisk(RiskLevel risk, DataSensitivity sensitivity) {
        return switch (sensitivity) {
            case RESTRICTED -> RiskLevel.HIGH;
            case CONFIDENTIAL -> risk.elevate();
            case PUBLIC, INTERNAL -> risk;
        };
    }

    private PolicySelection selection(
            RiskLevel risk, CryptoMode mode, String profile, String reason) {
        return new PolicySelection(risk, mode, profile, reason);
    }
}
