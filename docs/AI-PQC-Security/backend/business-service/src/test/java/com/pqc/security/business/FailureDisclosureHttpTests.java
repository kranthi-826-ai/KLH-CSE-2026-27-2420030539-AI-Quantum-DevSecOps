package com.pqc.security.business;

import com.pqc.security.business.service.AdaptiveSecurityService;
import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import com.pqc.security.business.security.AdaptiveSecurityFailure;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.client.RestClientException;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

@SpringBootTest(webEnvironment=SpringBootTest.WebEnvironment.RANDOM_PORT)
class FailureDisclosureHttpTests {
    @Value("${local.server.port}") int port;
    @Value("${security.jwt.secret}") String secret;
    @MockitoBean AdaptiveSecurityService service;
    @Autowired CryptoExecutionRepository repository;
    private static final String PRIVATE="SYNTHETIC_HTTP_PRIVATE_MARKER http://internal.invalid/?key=not-real";

    String token(String subject) {
        return Jwts.builder().subject(subject).claim("role","ROLE_USER")
                .expiration(new Date(System.currentTimeMillis()+60000))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).compact();
    }

    @ParameterizedTest
    @ValueSource(strings={"dependency","crypto","argument","reviewed-denial"})
    void actualHttpAdviceDoesNotDiscloseUnreviewedMessages(String category) throws Exception {
        Exception failure=switch(category) {
            case "dependency" -> new RestClientException(PRIVATE);
            case "argument" -> new IllegalArgumentException(PRIVATE);
            case "reviewed-denial" -> new AdaptiveSecurityFailure(AdaptiveSecurityFailure.Reason.HIGH_RISK_UNAVAILABLE);
            default -> new GeneralSecurityException(PRIVATE);
        };
        when(service.protect(any(),anyString(),any(),any())).thenThrow(failure);
        var request=HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+"/api/v1/business/adaptive-secure-data"))
                .header("Authorization","Bearer "+token("disclosure-fixture"))
                .header("Content-Type","application/json")
                .POST(HttpRequest.BodyPublishers.ofString("""
                  {"data":"synthetic","networkFeatures":{"dur":0.1},"dataSensitivity":"INTERNAL",
                   "hybridSupported":true,"pqcSupported":true,"maxCryptoLatencyMillis":100}
                  """)).build();
        var response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString());
        assertThat(response.statusCode()).isEqualTo(category.equals("dependency") ? 502 : 422);
        assertThat(response.body()).doesNotContain("SYNTHETIC_HTTP_PRIVATE_MARKER","internal.invalid","not-real");
        String expectedMessage=switch(category) {
            case "dependency" -> "Adaptive security dependency failed";
            case "argument" -> "Adaptive security request or cryptographic parameters are invalid";
            case "reviewed-denial" -> AdaptiveSecurityFailure.Reason.HIGH_RISK_UNAVAILABLE.publicMessage();
            default -> "Cryptographic verification or execution failed";
        };
        assertThat(response.body()).contains(expectedMessage,"message");
    }

    @Test void legacyDatabaseMessageIsNotReturnedByActualReadEndpoint() throws Exception {
        String owner="legacy_"+UUID.randomUUID().toString().substring(0,8);
        var entity=new CryptoExecutionEntity(UUID.randomUUID().toString(),Instant.now(),"legacy-disclosure",owner,"a".repeat(64));
        entity.fail(1,PRIVATE);
        repository.saveAndFlush(entity);
        var request=HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+"/api/v1/business/executions"))
                .header("Authorization","Bearer "+token(owner)).GET().build();
        var response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString());
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("Adaptive security operation failed")
                .doesNotContain("SYNTHETIC_HTTP_PRIVATE_MARKER","internal.invalid","not-real");
        assertThat(repository.findById(entity.getExecutionId()).orElseThrow().getErrorDetail()).isEqualTo(PRIVATE);
    }
}
