package com.pqc.security.policy.entity;

import com.pqc.security.policy.dto.PolicyDecisionRequest;
import com.pqc.security.policy.service.PolicyRules;
import com.pqc.security.policy.service.PolicySelection;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "policy_decisions")
public class PolicyDecisionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 36)
    private String decisionId;

    @Column(nullable = false)
    private Instant decidedAt;

    @Column(nullable = false, length = 20)
    private String inputRiskLevel;

    @Column(nullable = false, length = 20)
    private String effectiveRiskLevel;

    @Column(nullable = false)
    private double riskScore;

    @Column(nullable = false, length = 20)
    private String dataSensitivity;

    @Column(nullable = false)
    private boolean hybridSupported;

    @Column(nullable = false)
    private boolean pqcSupported;

    @Column(nullable = false)
    private long maxCryptoLatencyMillis;

    @Column(length = 500)
    private String riskExplanation;

    @Column(nullable = false, length = 20)
    private String selectedMode;

    @Column(nullable = false, length = 80)
    private String algorithmProfile;

    @Column(nullable = false, length = 500)
    private String reason;

    @Column(nullable = false, length = 20)
    private String policyVersion;

    @Column(length = 80)
    private String modelVersion;

    @Column(nullable = false, length = 80)
    private String sourceService;

    @Column(length = 80)
    private String correlationId;

    protected PolicyDecisionEntity() {
    }

    public PolicyDecisionEntity(PolicyDecisionRequest request, PolicySelection selection) {
        decisionId = UUID.randomUUID().toString();
        decidedAt = Instant.now();
        inputRiskLevel = request.riskLevel().name();
        effectiveRiskLevel = selection.effectiveRiskLevel().name();
        riskScore = request.riskScore();
        dataSensitivity = request.dataSensitivity().name();
        hybridSupported = request.hybridSupported();
        pqcSupported = request.pqcSupported();
        maxCryptoLatencyMillis = request.maxCryptoLatencyMillis();
        riskExplanation = request.riskExplanation();
        selectedMode = selection.mode().name();
        algorithmProfile = selection.algorithmProfile();
        reason = selection.reason();
        policyVersion = PolicyRules.VERSION;
        modelVersion = request.modelVersion();
        sourceService = request.sourceService();
        correlationId = request.correlationId();
    }

    public Long getId() { return id; }
    public String getDecisionId() { return decisionId; }
    public Instant getDecidedAt() { return decidedAt; }
    public String getInputRiskLevel() { return inputRiskLevel; }
    public String getEffectiveRiskLevel() { return effectiveRiskLevel; }
    public double getRiskScore() { return riskScore; }
    public String getDataSensitivity() { return dataSensitivity; }
    public boolean isHybridSupported() { return hybridSupported; }
    public boolean isPqcSupported() { return pqcSupported; }
    public long getMaxCryptoLatencyMillis() { return maxCryptoLatencyMillis; }
    public String getRiskExplanation() { return riskExplanation; }
    public String getSelectedMode() { return selectedMode; }
    public String getAlgorithmProfile() { return algorithmProfile; }
    public String getReason() { return reason; }
    public String getPolicyVersion() { return policyVersion; }
    public String getModelVersion() { return modelVersion; }
    public String getSourceService() { return sourceService; }
    public String getCorrelationId() { return correlationId; }
}
