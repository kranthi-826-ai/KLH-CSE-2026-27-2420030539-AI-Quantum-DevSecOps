package com.pqc.security.policy.service;

import com.pqc.security.policy.dto.PolicyDecisionRequest;
import com.pqc.security.policy.dto.PolicyDecisionResponse;
import com.pqc.security.policy.dto.NetworkPolicyRequest;
import com.pqc.security.policy.dto.AiPredictionResponse;
import com.pqc.security.policy.entity.PolicyDecisionEntity;
import com.pqc.security.policy.repository.PolicyDecisionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class PolicyDecisionService {

    private final PolicyRules rules;
    private final PolicyDecisionRepository repository;
    private final AiRiskClient aiRiskClient;

    public PolicyDecisionService(
            PolicyRules rules,
            PolicyDecisionRepository repository,
            AiRiskClient aiRiskClient) {
        this.rules = rules;
        this.repository = repository;
        this.aiRiskClient = aiRiskClient;
    }

    @Transactional
    public PolicyDecisionResponse decide(PolicyDecisionRequest request) {
        PolicySelection selection = rules.select(request);
        PolicyDecisionEntity saved = repository.save(new PolicyDecisionEntity(request, selection));
        return PolicyDecisionResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public List<PolicyDecisionResponse> latest() {
        return repository.findTop100ByOrderByDecidedAtDesc().stream()
                .map(PolicyDecisionResponse::from)
                .toList();
    }

    @Transactional
    public PolicyDecisionResponse evaluateNetwork(NetworkPolicyRequest request) {
        AiPredictionResponse prediction = aiRiskClient.predict(request);
        PolicyDecisionRequest decisionRequest = new PolicyDecisionRequest(
                prediction.riskLevel(),
                prediction.riskScore(),
                request.dataSensitivity(),
                request.hybridSupported(),
                request.pqcSupported(),
                request.maxCryptoLatencyMillis(),
                request.sourceService(),
                request.correlationId(),
                prediction.modelVersion(),
                prediction.explanation());
        return decide(decisionRequest);
    }
}
