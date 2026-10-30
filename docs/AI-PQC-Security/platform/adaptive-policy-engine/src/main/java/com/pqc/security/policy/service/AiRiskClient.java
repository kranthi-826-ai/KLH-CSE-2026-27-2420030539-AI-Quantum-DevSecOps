package com.pqc.security.policy.service;

import com.pqc.security.policy.dto.AiPredictionResponse;
import com.pqc.security.policy.dto.NetworkPolicyRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

import static org.springframework.http.HttpStatus.BAD_GATEWAY;

@Component
public class AiRiskClient {

    private final RestClient restClient;

    public AiRiskClient(
            @Value("${ai.security-service.url}") String serviceUrl,
            @Value("${internal.api-key}") String internalApiKey) {
        SimpleClientHttpRequestFactory transport = new SimpleClientHttpRequestFactory();
        transport.setConnectTimeout(java.time.Duration.ofSeconds(2));
        transport.setReadTimeout(java.time.Duration.ofSeconds(5));
        this.restClient = RestClient.builder()
                .requestFactory(transport)
                .baseUrl(serviceUrl)
                .defaultHeader("X-Internal-API-Key", internalApiKey)
                .build();
    }

    public AiPredictionResponse predict(NetworkPolicyRequest request) {
        try {
            AiPredictionResponse response = restClient.post()
                    .uri("/api/v1/ai/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of(
                            "features", request.features(),
                            "correlation_id", request.correlationId() == null ? "" : request.correlationId(),
                            "source_service", request.sourceService()))
                    .retrieve()
                    .body(AiPredictionResponse.class);
            if (response == null) {
                throw new ResponseStatusException(BAD_GATEWAY, "AI service returned no prediction");
            }
            validate(response, request.correlationId());
            return response;
        } catch (ResponseStatusException exception) {
            throw exception;
        } catch (RuntimeException exception) {
            throw new ResponseStatusException(BAD_GATEWAY, "AI security service is unavailable", exception);
        }
    }

    static void validate(AiPredictionResponse response, String correlation) {
        boolean invalid=response.predictedAttack()==null || response.riskScore()==null
            || !Double.isFinite(response.riskScore()) || response.riskScore()<0 || response.riskScore()>1
            || response.riskLevel()==null || response.modelVersion()==null
            || !response.modelVersion().matches("[0-9a-f]{16}")
            || response.modelName()==null || !response.modelName().matches("[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
            || response.explanation()==null || response.explanation().isBlank() || response.explanation().length()>500
            || !java.util.Objects.equals(correlation==null ? "" : correlation,response.correlationId());
        if (!invalid) {
            var expected=response.riskScore()>=.70 ? com.pqc.security.policy.domain.RiskLevel.HIGH
                : response.riskScore()>=.35 ? com.pqc.security.policy.domain.RiskLevel.MEDIUM
                : com.pqc.security.policy.domain.RiskLevel.LOW;
            invalid=response.riskLevel()!=expected;
        }
        if (invalid) throw new ResponseStatusException(BAD_GATEWAY,"AI prediction response is invalid");
    }
}
