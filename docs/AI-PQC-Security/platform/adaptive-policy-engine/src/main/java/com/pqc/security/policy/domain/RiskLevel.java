package com.pqc.security.policy.domain;

public enum RiskLevel {
    LOW,
    MEDIUM,
    HIGH;

    public RiskLevel elevate() {
        return switch (this) {
            case LOW -> MEDIUM;
            case MEDIUM, HIGH -> HIGH;
        };
    }
}
