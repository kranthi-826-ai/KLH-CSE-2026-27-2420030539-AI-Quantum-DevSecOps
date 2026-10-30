package com.pqc.security.business.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "crypto_executions")
public class CryptoExecutionEntity {
    @Id
    @Column(length = 36, nullable = false)
    private String executionId;
    @Column(nullable = false)
    private Instant executedAt;
    @Column(length = 36)
    private String decisionId;
    @Column(length = 80, nullable = false)
    private String correlationId;
    @Column(length = 100)
    private String username;
    @Column(length = 64, nullable = false)
    private String payloadSha256;
    @Column(length = 20)
    private String riskLevel;
    private double riskScore;
    @Column(length = 20)
    private String selectedMode;
    @Column(length = 120)
    private String algorithmProfile;
    @Column(length = 500)
    private String selectionReason;
    @Column(length = 40)
    private String policyVersion;
    @Column(length = 80)
    private String modelVersion;
    private long policyLatencyMillis;
    private long cryptoLatencyMillis;
    private long totalLatencyMillis;
    private boolean roundTripVerified;
    @Column(length = 20, nullable = false)
    private String outcome;
    @Column(length = 500)
    private String errorDetail;

    protected CryptoExecutionEntity() { }

    public CryptoExecutionEntity(String executionId, Instant executedAt, String correlationId,
                                 String username, String payloadSha256) {
        this.executionId = executionId;
        this.executedAt = executedAt;
        this.correlationId = correlationId;
        this.username = username;
        this.payloadSha256 = payloadSha256;
        this.outcome = "STARTED";
    }

    public void complete(String decisionId, String riskLevel, double riskScore, String selectedMode,
                         String algorithmProfile, String selectionReason, String policyVersion, String modelVersion,
                         long policyLatencyMillis, long cryptoLatencyMillis, long totalLatencyMillis,
                         boolean verified) {
        recordDecision(decisionId, riskLevel, riskScore, selectedMode, algorithmProfile,
                selectionReason, policyVersion, modelVersion);
        this.policyLatencyMillis = policyLatencyMillis;
        this.cryptoLatencyMillis = cryptoLatencyMillis;
        this.totalLatencyMillis = totalLatencyMillis;
        this.roundTripVerified = verified;
        this.outcome = verified ? "SUCCESS" : "FAILED";
    }

    public void recordDecision(String decisionId, String riskLevel, double riskScore, String selectedMode,
                               String algorithmProfile, String selectionReason,
                               String policyVersion, String modelVersion) {
        this.decisionId = decisionId;
        this.riskLevel = riskLevel;
        this.riskScore = riskScore;
        this.selectedMode = selectedMode;
        this.algorithmProfile = algorithmProfile;
        this.selectionReason = selectionReason;
        this.policyVersion = policyVersion;
        this.modelVersion = modelVersion;
    }

    public void fail(long totalLatencyMillis, String errorDetail) {
        this.totalLatencyMillis = totalLatencyMillis;
        this.outcome = "FAILED";
        this.errorDetail = errorDetail == null ? "Unknown error" : errorDetail.substring(0, Math.min(500, errorDetail.length()));
    }

    public String getExecutionId() { return executionId; }
    public Instant getExecutedAt() { return executedAt; }
    public String getDecisionId() { return decisionId; }
    public String getCorrelationId() { return correlationId; }
    public String getUsername() { return username; }
    public String getRiskLevel() { return riskLevel; }
    public double getRiskScore() { return riskScore; }
    public String getSelectedMode() { return selectedMode; }
    public String getAlgorithmProfile() { return algorithmProfile; }
    public String getSelectionReason() { return selectionReason; }
    public String getPolicyVersion() { return policyVersion; }
    public String getModelVersion() { return modelVersion; }
    public long getPolicyLatencyMillis() { return policyLatencyMillis; }
    public long getCryptoLatencyMillis() { return cryptoLatencyMillis; }
    public long getTotalLatencyMillis() { return totalLatencyMillis; }
    public boolean isRoundTripVerified() { return roundTripVerified; }
    public String getOutcome() { return outcome; }
    public String getErrorDetail() { return errorDetail; }
}
