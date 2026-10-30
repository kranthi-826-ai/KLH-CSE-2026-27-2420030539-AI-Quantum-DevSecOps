package com.pqc.security.gateway.filter;

import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DependencyFailureFilterTests {
    @Test void discoveryUnavailableIs503NotGeneric500AndDoesNotLeakInternalDetails() throws Exception {
        var request = new MockHttpServletRequest("GET", "/api/v1/business/secure-data");
        var response = new MockHttpServletResponse();
        response.setHeader("X-Correlation-ID", "test-correlation");
        new DependencyFailureFilter().doFilter(request, response, (req, res) -> {
            throw new ServletException(new HttpServerErrorException(HttpStatus.SERVICE_UNAVAILABLE, "internal-host:secret"));
        });
        assertThat(response.getStatus()).isEqualTo(503);
        assertThat(response.getHeader("X-Correlation-ID")).isEqualTo("test-correlation");
        assertThat(response.getHeader("Cache-Control")).isEqualTo("no-store");
        assertThat(response.getHeader("Retry-After")).isEqualTo("2");
        assertThat(response.getContentAsString()).contains("backend service is unavailable").doesNotContain("internal-host", "secret");
    }

    @Test void transportFailureIsUnavailable() throws Exception {
        var response = new MockHttpServletResponse();
        new DependencyFailureFilter().doFilter(new MockHttpServletRequest("GET", "/api/v1/events"), response,
                (req, res) -> { throw new ResourceAccessException("internal address"); });
        assertThat(response.getStatus()).isEqualTo(503);
    }

    @Test void unrelatedProgrammingErrorIsNotHiddenAsDependencyFailure() {
        assertThatThrownBy(() -> new DependencyFailureFilter().doFilter(
                new MockHttpServletRequest("GET", "/api/v1/events"), new MockHttpServletResponse(),
                (req, res) -> { throw new IllegalStateException("bug"); })).isInstanceOf(IllegalStateException.class);
    }

    @Test void doesNotRewriteAlreadyCommittedResponse() {
        var response = new MockHttpServletResponse();
        response.setCommitted(true);
        assertThatThrownBy(() -> new DependencyFailureFilter().doFilter(
                new MockHttpServletRequest("GET", "/api/v1/events"), response,
                (req, res) -> { throw new ResourceAccessException("unavailable"); })).isInstanceOf(ResourceAccessException.class);
    }
}
