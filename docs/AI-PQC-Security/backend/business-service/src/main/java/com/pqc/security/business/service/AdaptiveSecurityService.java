package com.pqc.security.business.service;

import com.pqc.security.business.client.AdaptivePolicyClient;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.dto.AdaptiveSecureResponse;
import com.pqc.security.business.dto.PolicyDecision;
import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.security.AdaptiveSecurityFailure;
import com.pqc.security.business.security.PublicFailureMessages;
import static com.pqc.security.business.security.AdaptiveSecurityFailure.Reason.*;
import com.pqc.security.crypto.api.CryptoKeyPair;
import com.pqc.security.crypto.api.SecureEnvelope;
import com.pqc.security.crypto.api.CryptoProfiles;
import com.pqc.security.crypto.hybrid.CryptoProfile;
import com.pqc.security.crypto.hybrid.CryptoProfileFactory;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;

@Service
public class AdaptiveSecurityService {

    private final AdaptivePolicyClient policyClient;
    private final ExecutionAuditWriter auditWriter;
    private final MeterRegistry meterRegistry;

    public AdaptiveSecurityService(AdaptivePolicyClient policyClient,
                                   ExecutionAuditWriter auditWriter,
                                   MeterRegistry meterRegistry) {
        this.policyClient = policyClient;
        this.auditWriter = auditWriter;
        this.meterRegistry = meterRegistry;
        meterRegistry.counter("adaptive_security_failure_audit_errors_total");
    }

    public AdaptiveSecureResponse protect(AdaptiveSecureRequest request, String username,
                                          String suppliedCorrelationId) throws GeneralSecurityException {
        return protect(request, username, suppliedCorrelationId, null);
    }

    public AdaptiveSecureResponse protect(AdaptiveSecureRequest request, String username,
                                          String suppliedCorrelationId, String sourceIp) throws GeneralSecurityException {
        long started = System.nanoTime();
        String correlationId = hasText(suppliedCorrelationId) ? suppliedCorrelationId : UUID.randomUUID().toString();
        String executionId = UUID.randomUUID().toString();
        byte[] plaintext = request.data().getBytes(StandardCharsets.UTF_8);
        CryptoExecutionEntity audit = new CryptoExecutionEntity(executionId, java.time.Instant.now(),
                correlationId, username, sha256(plaintext));
        try {
            auditWriter.save(audit, sourceIp);
            long policyStarted = System.nanoTime();
            PolicyDecision decision = policyClient.evaluate(request, correlationId);
            long policyMillis = elapsedMillis(policyStarted);

            if (decision == null) {
                throw new AdaptiveSecurityFailure(NO_DECISION);
            }
            validateDecision(decision, correlationId, request);
            audit.recordDecision(decision.decisionId(), decision.effectiveRiskLevel(), decision.riskScore(),
                    decision.selectedMode(), decision.algorithmProfile(), decision.reason(),
                    decision.policyVersion(), decision.modelVersion());
            if ("HIGH".equals(decision.effectiveRiskLevel()) && "CLASSICAL".equals(decision.selectedMode())) {
                throw new AdaptiveSecurityFailure(HIGH_RISK_UNAVAILABLE);
            }

            long cryptoStarted = System.nanoTime();
            CryptoProfile profile = CryptoProfileFactory.create(decision.algorithmProfile());
            CryptoKeyPair recipient = profile.kem().generateKeyPair();
            CryptoKeyPair signer = profile.signatures().generateKeyPair();
            byte[] aad = (executionId + ":" + correlationId + ":" + decision.decisionId())
                    .getBytes(StandardCharsets.UTF_8);
            SecureEnvelope envelope = profile.envelopeService().seal(
                    recipient.publicKey(), signer.privateKey(), plaintext, aad);
            byte[] verifiedPlaintext = profile.envelopeService().open(
                    recipient.privateKey(), signer.publicKey(), envelope, aad);
            boolean verified = MessageDigest.isEqual(plaintext, verifiedPlaintext);
            Arrays.fill(verifiedPlaintext, (byte) 0);
            long cryptoMillis = elapsedMillis(cryptoStarted);
            long totalMillis = elapsedMillis(started);

            audit.complete(decision.decisionId(), decision.effectiveRiskLevel(), decision.riskScore(),
                    decision.selectedMode(), decision.algorithmProfile(), decision.reason(), decision.policyVersion(),
                    decision.modelVersion(), policyMillis, cryptoMillis, totalMillis, verified);
            if (!verified) throw new AdaptiveSecurityFailure(ROUND_TRIP_FAILED);
            auditWriter.save(audit, sourceIp);
            meterRegistry.counter("adaptive_security_executions_total",
                    "outcome", verified ? "success" : "failed",
                    "mode", decision.selectedMode(),
                    "risk", decision.effectiveRiskLevel()).increment();
            Timer.builder("adaptive_security_flow_duration")
                    .description("End-to-end adaptive policy and cryptographic execution time")
                    .tag("mode", decision.selectedMode())
                    .register(meterRegistry)
                    .record(java.time.Duration.ofMillis(totalMillis));

            Base64.Encoder encoder = Base64.getEncoder();
            return new AdaptiveSecureResponse(executionId, decision.decisionId(), correlationId,
                    decision.effectiveRiskLevel(), decision.riskScore(), decision.selectedMode(),
                    decision.algorithmProfile(), decision.policyVersion(), decision.modelVersion(),
                    encoder.encodeToString(envelope.payload().ciphertext()),
                    encoder.encodeToString(envelope.payload().nonce()),
                    encoder.encodeToString(envelope.encapsulation()),
                    encoder.encodeToString(envelope.signature()), true,
                    policyMillis, cryptoMillis, totalMillis);
        } catch (GeneralSecurityException | RuntimeException exception) {
            audit.fail(elapsedMillis(started), PublicFailureMessages.describe(exception));
            meterRegistry.counter("adaptive_security_executions_total",
                    "outcome", "failed",
                    "mode", hasText(audit.getSelectedMode()) ? audit.getSelectedMode() : "unselected",
                    "risk", hasText(audit.getRiskLevel()) ? audit.getRiskLevel() : "unknown").increment();
            try {
                auditWriter.save(audit, sourceIp);
            } catch (RuntimeException auditFailure) {
                // Never return an envelope or invent a persisted FAILED record when
                // storage is unavailable. Preserve the primary operation failure.
                meterRegistry.counter("adaptive_security_failure_audit_errors_total").increment();
                if (auditFailure != exception) exception.addSuppressed(auditFailure);
            }
            throw exception;
        } finally {
            Arrays.fill(plaintext, (byte) 0);
        }
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private static void validateDecision(PolicyDecision decision, String correlationId, AdaptiveSecureRequest request)
            throws GeneralSecurityException {
        if (!hasText(decision.decisionId()) || !correlationId.equals(decision.correlationId())) {
            throw new AdaptiveSecurityFailure(IDENTITY_MISMATCH);
        }
        if (decision.riskScore()==null || !Double.isFinite(decision.riskScore()) || decision.riskScore() < 0 || decision.riskScore() > 1) {
            throw new AdaptiveSecurityFailure(INVALID_SCORE);
        }
        if (!"LOW".equals(decision.effectiveRiskLevel()) && !"MEDIUM".equals(decision.effectiveRiskLevel())
                && !"HIGH".equals(decision.effectiveRiskLevel())) {
            throw new AdaptiveSecurityFailure(INVALID_EFFECTIVE_RISK);
        }
        String expectedProfile = switch (decision.selectedMode() == null ? "" : decision.selectedMode()) {
            case "CLASSICAL" -> CryptoProfiles.CLASSICAL;
            case "HYBRID" -> CryptoProfiles.HYBRID;
            case "PQC" -> CryptoProfiles.PQC;
            default -> throw new AdaptiveSecurityFailure(UNKNOWN_MODE);
        };
        if (!expectedProfile.equals(decision.algorithmProfile())) {
            throw new AdaptiveSecurityFailure(PROFILE_MISMATCH);
        }
        String inputRisk=decision.riskScore()>=.70 ? "HIGH" : decision.riskScore()>=.35 ? "MEDIUM" : "LOW";
        if (!inputRisk.equals(decision.inputRiskLevel())) {
            throw new AdaptiveSecurityFailure(INPUT_RISK_MISMATCH);
        }
        String effectiveRisk=switch(request.dataSensitivity().toUpperCase(java.util.Locale.ROOT)) {
            case "RESTRICTED" -> "HIGH";
            case "CONFIDENTIAL" -> "LOW".equals(inputRisk) ? "MEDIUM" : "HIGH";
            case "PUBLIC", "INTERNAL" -> inputRisk;
            default -> throw new AdaptiveSecurityFailure(UNSUPPORTED_SENSITIVITY);
        };
        if (!effectiveRisk.equals(decision.effectiveRiskLevel())) {
            throw new AdaptiveSecurityFailure(EFFECTIVE_RISK_MISMATCH);
        }
        if (("HYBRID".equals(decision.selectedMode()) && !request.hybridSupported())
            || ("PQC".equals(decision.selectedMode()) && !request.pqcSupported())) {
            throw new AdaptiveSecurityFailure(INCOMPATIBLE_MODE);
        }
        if (!"1.1.0".equals(decision.policyVersion()) || decision.modelVersion()==null
            || !decision.modelVersion().matches("[A-Za-z0-9._-]{1,80}")
            || !hasText(decision.reason()) || decision.reason().length()>500
            || decision.decisionId().length()>36) {
            throw new AdaptiveSecurityFailure(INVALID_PROVENANCE);
        }
    }

    private static long elapsedMillis(long startNanos) {
        return (System.nanoTime() - startNanos) / 1_000_000;
    }

    private static String sha256(byte[] value) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
        } catch (GeneralSecurityException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
