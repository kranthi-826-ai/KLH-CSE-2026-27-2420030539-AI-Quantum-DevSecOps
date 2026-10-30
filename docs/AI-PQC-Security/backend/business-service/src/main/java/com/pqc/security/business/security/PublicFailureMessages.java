package com.pqc.security.business.security;

import java.security.GeneralSecurityException;
import org.springframework.web.client.RestClientException;
import java.util.Set;
import java.util.Arrays;

/** Shared disclosure boundary for the HTTP body and persisted execution reason. */
public final class PublicFailureMessages {
    private static final Set<String> GENERIC = Set.of("Adaptive security dependency failed",
            "Cryptographic verification or execution failed",
            "Adaptive security request or cryptographic parameters are invalid",
            "Adaptive security operation failed");
    private PublicFailureMessages() { }
    public static String describe(Exception failure) {
        if (failure instanceof AdaptiveSecurityFailure reviewed) return reviewed.reason().publicMessage();
        if (failure instanceof RestClientException) return "Adaptive security dependency failed";
        if (failure instanceof GeneralSecurityException) return "Cryptographic verification or execution failed";
        if (failure instanceof IllegalArgumentException) return "Adaptive security request or cryptographic parameters are invalid";
        return "Adaptive security operation failed";
    }

    /** Preserve stored evidence, but never expose arbitrary legacy exception strings. */
    public static String forStoredDetail(String detail) {
        if (detail == null) return null;
        if (GENERIC.contains(detail) || Arrays.stream(AdaptiveSecurityFailure.Reason.values())
                .anyMatch(reason -> reason.publicMessage().equals(detail))) return detail;
        return "Adaptive security operation failed";
    }
}
