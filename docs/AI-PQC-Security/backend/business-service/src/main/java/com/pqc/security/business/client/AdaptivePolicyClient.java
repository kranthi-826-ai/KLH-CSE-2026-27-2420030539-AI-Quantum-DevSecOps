package com.pqc.security.business.client;

import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.dto.PolicyDecision;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.LinkedHashMap;
import java.util.Map;

@Component
public class AdaptivePolicyClient {

    private final RestClient restClient;

    public AdaptivePolicyClient(
            @Value("${adaptive-policy.url}") String serviceUrl,
            @Value("${adaptive-policy.api-key}") String apiKey) {
        SimpleClientHttpRequestFactory transport = new SimpleClientHttpRequestFactory();
        transport.setConnectTimeout(java.time.Duration.ofSeconds(2));
        transport.setReadTimeout(java.time.Duration.ofSeconds(5));
        this.restClient = RestClient.builder()
                .requestFactory(transport)
                .baseUrl(serviceUrl)
                .defaultHeader("X-Internal-API-Key", apiKey)
                .build();
    }

    public PolicyDecision evaluate(AdaptiveSecureRequest request, String correlationId) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("features", request.networkFeatures());
        body.put("dataSensitivity", request.dataSensitivity().toUpperCase(java.util.Locale.ROOT));
        body.put("hybridSupported", request.hybridSupported());
        body.put("pqcSupported", request.pqcSupported());
        body.put("maxCryptoLatencyMillis", request.maxCryptoLatencyMillis());
        body.put("sourceService", "business-service");
        body.put("correlationId", correlationId);

        PolicyDecision decision = restClient.post()
                .uri("/api/v1/policies/decisions/evaluate-network")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .body(PolicyDecision.class);
        if (decision == null) {
            throw new IllegalStateException("Adaptive policy engine returned no decision");
        }
        return decision;
    }
}
