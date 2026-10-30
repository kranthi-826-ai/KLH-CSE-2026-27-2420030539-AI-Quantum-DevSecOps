package com.pqc.security.policy.security;

import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.assertj.core.api.Assertions.assertThat;

class InternalApiKeyFilterTests {

    private final InternalApiKeyFilter filter = new InternalApiKeyFilter("expected-key");

    @Test
    void acceptsMatchingKeyForPolicyEndpoint() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest(
                "POST", "/api/v1/policies/decisions");
        request.addHeader("X-Internal-API-Key", "expected-key");
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicBoolean continued = new AtomicBoolean();
        filter.doFilter(request, response,
                (ignoredRequest, ignoredResponse) -> continued.set(true));
        assertThat(continued).isTrue();
    }

    @Test
    void rejectsMissingKeyForPolicyEndpoint() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest(
                "POST", "/api/v1/policies/decisions");
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicBoolean continued = new AtomicBoolean();
        filter.doFilter(request, response,
                (ignoredRequest, ignoredResponse) -> continued.set(true));
        assertThat(continued).isFalse();
        assertThat(response.getStatus()).isEqualTo(401);
    }
}
