package com.pqc.security.business.security;

import java.security.GeneralSecurityException;
import java.util.Objects;

/** Reviewed failures with fixed public text; never interpolate dependency data. */
public final class AdaptiveSecurityFailure extends GeneralSecurityException {
    public enum Reason {
        NO_DECISION("Policy engine returned no decision"),
        HIGH_RISK_UNAVAILABLE("High-risk operation denied: quantum-resilient protection is unavailable"),
        ROUND_TRIP_FAILED("Cryptographic round-trip verification failed"),
        IDENTITY_MISMATCH("Policy decision identity or correlation mismatch"),
        INVALID_SCORE("Invalid policy risk score"),
        INVALID_EFFECTIVE_RISK("Invalid effective policy risk"),
        UNKNOWN_MODE("Unknown cryptographic policy mode"),
        PROFILE_MISMATCH("Cryptographic mode and algorithm profile disagree"),
        INPUT_RISK_MISMATCH("Policy input risk and model score disagree"),
        UNSUPPORTED_SENSITIVITY("Unsupported request sensitivity"),
        EFFECTIVE_RISK_MISMATCH("Policy effective risk contradicts request sensitivity"),
        INCOMPATIBLE_MODE("Policy selected an incompatible cryptographic mode"),
        INVALID_PROVENANCE("Policy decision provenance is invalid");

        private final String publicMessage;
        Reason(String publicMessage) { this.publicMessage = publicMessage; }
        public String publicMessage() { return publicMessage; }
    }

    private final Reason reason;
    public AdaptiveSecurityFailure(Reason reason) {
        super(Objects.requireNonNull(reason).publicMessage());
        this.reason = reason;
    }
    public Reason reason() { return reason; }
}
