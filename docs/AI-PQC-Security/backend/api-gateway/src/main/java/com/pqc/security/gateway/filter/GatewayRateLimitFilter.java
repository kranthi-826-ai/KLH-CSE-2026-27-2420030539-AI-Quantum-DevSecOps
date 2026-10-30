package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.MeterRegistry;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class GatewayRateLimitFilter extends OncePerRequestFilter {
    private final LocalRateLimiter api;
    private final LocalRateLimiter authentication;
    private final MeterRegistry meters;

    public GatewayRateLimitFilter(
            @Value("${security.rate-limit.api-capacity:120}") int apiCapacity,
            @Value("${security.rate-limit.api-period-seconds:60}") long apiPeriod,
            @Value("${security.rate-limit.auth-capacity:10}") int authCapacity,
            @Value("${security.rate-limit.auth-period-seconds:60}") long authPeriod,
            @Value("${security.rate-limit.max-clients:10000}") int maxClients,
            MeterRegistry meters) {
        api = new LocalRateLimiter(apiCapacity, apiPeriod, maxClients, System::nanoTime);
        authentication = new LocalRateLimiter(authCapacity, authPeriod, maxClients, System::nanoTime);
        this.meters = meters;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !request.getRequestURI().startsWith(request.getContextPath() + "/api/v1/")
                || "OPTIONS".equals(request.getMethod());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                   FilterChain chain) throws ServletException, IOException {
        // Use the actual peer address; untrusted forwarding headers must not
        // permit a caller to manufacture unlimited identities.
        String client = request.getRemoteAddr();
        LocalRateLimiter.Decision decision = api.acquire(client);
        String scope = "api";
        String path = request.getRequestURI().substring(request.getContextPath().length());
        if (decision.allowed() && (path.equals("/api/v1/auth/login")
                || path.equals("/api/v1/auth/register"))) {
            decision = authentication.acquire(client);
            scope = "authentication";
        }
        if (decision.allowed()) {
            chain.doFilter(request, response);
            return;
        }
        boolean full = decision.capacityExceeded();
        meters.counter("gateway_requests_rejected_total", "scope", scope,
                "reason", full ? "client_capacity" : "rate_limit").increment();
        response.setStatus(full ? 503 : 429);
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Retry-After", Long.toString(decision.retryAfterSeconds()));
        response.setHeader("Cache-Control", "no-store");
        response.getWriter().write(full
                ? "{\"status\":503,\"error\":\"Service Unavailable\",\"message\":\"Gateway request capacity reached; retry later\"}"
                : "{\"status\":429,\"error\":\"Too Many Requests\",\"message\":\"Request rate limit exceeded; retry later\"}");
    }
}
