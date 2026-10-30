package com.pqc.security.policy.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.pqc.security.policy.domain.RiskLevel;

public record AiPredictionResponse(
        @JsonProperty("predicted_attack") Boolean predictedAttack,
        @JsonProperty("risk_score") Double riskScore,
        @JsonProperty("risk_level") RiskLevel riskLevel,
        @JsonProperty("model_version") String modelVersion,
        @JsonProperty("model_name") String modelName,
        @JsonProperty("correlation_id") String correlationId,
        String explanation) {
}
