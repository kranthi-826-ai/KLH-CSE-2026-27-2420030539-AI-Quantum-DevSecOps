package com.pqc.security.business.service;

import com.pqc.security.business.client.AdaptivePolicyClient;
import com.pqc.security.business.controller.AdaptiveSecurityExceptionHandler;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.event.SecurityEventPublisher;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.security.GeneralSecurityException;
import java.util.Map;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.ArgumentCaptor;
import org.springframework.web.client.RestClientException;
import com.pqc.security.business.dto.CryptoExecutionResponse;
import com.pqc.security.business.security.AdaptiveSecurityFailure;
import com.pqc.security.business.security.PublicFailureMessages;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.provider.EnumSource;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

class FailureDisclosureTests {
    private static final String PRIVATE = "SYNTHETIC_PRIVATE_MARKER http://internal.invalid/path?key=not-a-real-secret response-body";

    @ParameterizedTest
    @ValueSource(strings={"dependency","argument","unexpected"})
    void failedExecutionDoesNotPersistUntrustedExceptionText(String category) {
        var client=mock(AdaptivePolicyClient.class);
        RuntimeException failure=switch(category) {
            case "dependency" -> new RestClientException(PRIVATE);
            case "argument" -> new IllegalArgumentException(PRIVATE);
            default -> new IllegalStateException(PRIVATE);
        };
        when(client.evaluate(any(),anyString())).thenThrow(failure);
        var repository=mock(CryptoExecutionRepository.class);
        var service=new AdaptiveSecurityService(client,new ExecutionAuditWriter(repository,
                mock(SecurityEventPublisher.class)),new SimpleMeterRegistry());
        var request=new AdaptiveSecureRequest("synthetic payload",Map.of("dur",.1),"INTERNAL",true,true,100);
        assertThatThrownBy(()->service.protect(request,"fixture","disclosure-test")).isSameAs(failure);
        var audit=ArgumentCaptor.forClass(CryptoExecutionEntity.class);
        verify(repository,times(2)).save(audit.capture());
        assertThat(audit.getValue().getOutcome()).isEqualTo("FAILED");
        assertThat(audit.getValue().isRoundTripVerified()).isFalse();
        assertThat(audit.getValue().getErrorDetail()).isNotBlank()
                .doesNotContain("SYNTHETIC_PRIVATE_MARKER","internal.invalid","response-body","not-a-real-secret");
    }

    @ParameterizedTest
    @ValueSource(strings={"crypto","argument"})
    void publicErrorBodyDoesNotEchoProviderOrArgumentMessages(String category) {
        Exception failure=category.equals("crypto") ? new GeneralSecurityException(PRIVATE)
                : new IllegalArgumentException(PRIVATE);
        var response=new AdaptiveSecurityExceptionHandler().cryptoFailure(failure);
        assertThat(response.getStatusCode().value()).isEqualTo(422);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().get("message").toString()).isNotBlank()
                .doesNotContain("SYNTHETIC_PRIVATE_MARKER","internal.invalid","response-body","not-a-real-secret");
    }

    @ParameterizedTest
    @EnumSource(AdaptiveSecurityFailure.Reason.class)
    void reviewedReasonsRemainUsefulWithoutDisclosingExceptionCauses(AdaptiveSecurityFailure.Reason reason) {
        var failure=new AdaptiveSecurityFailure(reason);
        failure.initCause(new IllegalStateException(PRIVATE));
        assertThat(PublicFailureMessages.describe(failure)).isEqualTo(reason.publicMessage());
        assertThat(PublicFailureMessages.forStoredDetail(reason.publicMessage())).isEqualTo(reason.publicMessage());
    }

    @Test void legacyPrivateDetailsAreRedactedInReadDtoWithoutMutatingStoredEvidence() {
        var audit=new CryptoExecutionEntity("fixture",java.time.Instant.now(),"correlation","owner","a".repeat(64));
        audit.fail(1,PRIVATE);
        assertThat(CryptoExecutionResponse.from(audit).errorDetail()).isEqualTo("Adaptive security operation failed");
        assertThat(audit.getErrorDetail()).isEqualTo(PRIVATE);
        assertThat(PublicFailureMessages.forStoredDetail(null)).isNull();
        assertThat(PublicFailureMessages.forStoredDetail("High-risk operation denied: " + PRIVATE))
                .isEqualTo("Adaptive security operation failed");
    }
}
