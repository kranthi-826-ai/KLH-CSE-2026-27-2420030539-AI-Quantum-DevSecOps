package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.assertThat;

class GatewayRateLimitFilterTests {
    @Test void repeatedLoginIsRejectedDespiteForgedForwardingHeaders() throws Exception {
        SimpleMeterRegistry meters = new SimpleMeterRegistry();
        GatewayRateLimitFilter filter = new GatewayRateLimitFilter(120, 60, 2, 3600, 100, meters);
        AtomicInteger forwarded = new AtomicInteger();
        MockHttpServletResponse response = null;
        for (int i = 0; i < 3; i++) {
            var request = new MockHttpServletRequest("POST", "/api/v1/auth/login");
            request.setRemoteAddr("192.0.2.1");
            request.addHeader("X-Forwarded-For", "198.51.100." + i);
            response = new MockHttpServletResponse();
            filter.doFilter(request, response, (req, res) -> forwarded.incrementAndGet());
        }
        assertThat(forwarded.get()).isEqualTo(2);
        assertThat(response.getStatus()).isEqualTo(429);
        assertThat(response.getHeader("Retry-After")).isNotBlank();
        assertThat(response.getContentAsString()).contains("Too Many Requests");
        assertThat(meters.get("gateway_requests_rejected_total").counter().count()).isEqualTo(1);
    }

    @Test void limitsBusinessRequestsAndKeepsPeerBucketsSeparate() throws Exception {
        GatewayRateLimitFilter filter = new GatewayRateLimitFilter(1, 3600, 1, 3600, 100, new SimpleMeterRegistry());
        AtomicInteger forwarded = new AtomicInteger();
        for (String peer : new String[]{"192.0.2.1", "192.0.2.1", "192.0.2.2"}) {
            var request = new MockHttpServletRequest("GET", "/api/v1/business/secure-data");
            request.setRemoteAddr(peer);
            filter.doFilter(request, new MockHttpServletResponse(), (req, res) -> forwarded.incrementAndGet());
        }
        assertThat(forwarded.get()).isEqualTo(2);
    }

    @Test void healthChecksAreNotThrottled() throws Exception {
        GatewayRateLimitFilter filter = new GatewayRateLimitFilter(1, 3600, 1, 3600, 1, new SimpleMeterRegistry());
        AtomicInteger forwarded = new AtomicInteger();
        for (int i = 0; i < 3; i++) {
            filter.doFilter(new MockHttpServletRequest("GET", "/actuator/health"),
                    new MockHttpServletResponse(), (req, res) -> forwarded.incrementAndGet());
        }
        assertThat(forwarded.get()).isEqualTo(3);
    }
}
