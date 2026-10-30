package com.pqc.security.gateway.filter;
import com.pqc.security.http.RequestBoundaryFilter;

import jakarta.servlet.ServletException;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class CorrelationIdFilterTests {

    private final RequestBoundaryFilter filter = new RequestBoundaryFilter();

    @Test
    void generatesAndForwardsCorrelationIdWhenMissing() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicReference<String> forwardedId = new AtomicReference<>();

        filter.doFilter(request, response, (wrappedRequest, ignoredResponse) ->
                forwardedId.set(((MockHttpServletRequest) request).getHeader(
                        RequestBoundaryFilter.CORRELATION_ID_HEADER) == null
                        ? ((jakarta.servlet.http.HttpServletRequest) wrappedRequest)
                                .getHeader(RequestBoundaryFilter.CORRELATION_ID_HEADER)
                        : null));

        assertThat(forwardedId.get()).isNotBlank();
        assertThat(response.getHeader(RequestBoundaryFilter.CORRELATION_ID_HEADER))
                .isEqualTo(forwardedId.get());
    }

    @Test
    void preservesClientProvidedCorrelationId() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader(RequestBoundaryFilter.CORRELATION_ID_HEADER, "test-correlation-id");
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicReference<String> forwardedId = new AtomicReference<>();

        filter.doFilter(request, response, (wrappedRequest, ignoredResponse) ->
                forwardedId.set(((jakarta.servlet.http.HttpServletRequest) wrappedRequest)
                        .getHeader(RequestBoundaryFilter.CORRELATION_ID_HEADER)));

        assertThat(forwardedId.get()).isEqualTo("test-correlation-id");
        assertThat(response.getHeader(RequestBoundaryFilter.CORRELATION_ID_HEADER))
                .isEqualTo("test-correlation-id");
    }
}
