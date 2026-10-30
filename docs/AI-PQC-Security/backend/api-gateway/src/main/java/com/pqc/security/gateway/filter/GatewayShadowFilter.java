package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.MeterRegistry;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;

/** Observer only; does not modify the request, response, authentication or rate limiter. */
@Component
@ConditionalOnProperty(name = "security.shadow.enabled", havingValue = "true")
@Order(Ordered.HIGHEST_PRECEDENCE + 5)
public final class GatewayShadowFilter extends OncePerRequestFilter {
    private final ShadowRequestHistory history;
    private final ShadowObservationWriter writer;
    private final MeterRegistry meters;
    @Value("${security.shadow.expose-observation-id:false}") private boolean exposeObservationId;
    @Value("${security.shadow.feature-version:v1}") private String featureVersion = "v1";
    @jakarta.annotation.PostConstruct void validateVersion() {
        if (!java.util.Set.of("v1", "v2").contains(featureVersion)) throw new IllegalArgumentException("Unsupported shadow feature version");
    }
    public GatewayShadowFilter(ShadowObservationWriter writer, MeterRegistry meters,
            @Value("${security.shadow.max-peers:1024}") int maxPeers,
            @Value("${security.shadow.max-events-per-peer:128}") int maxEvents) {
        this.writer = writer;
        this.meters = meters;
        history = new ShadowRequestHistory(maxPeers, maxEvents);
    }
    @Override protected boolean shouldNotFilter(HttpServletRequest request) {
        String route = request.getRequestURI().substring(request.getContextPath().length());
        return !(route.equals("/api/v1/auth/login") && request.getMethod().equals("POST"))
                && !(route.equals("/api/v1/auth/me") && request.getMethod().equals("GET"));
    }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
            FilterChain chain) throws ServletException, IOException {
        String address = request.getRemoteAddr(); // Never trust X-Forwarded-For / client session IDs.
        String route = request.getRequestURI().substring(request.getContextPath().length());
        String authorization = request.getHeader("Authorization");
        long start = System.nanoTime();
        ShadowRequestHistory.Snapshot snapshot = null;
        boolean historyFailed = false;
        try {
            snapshot = featureVersion.equals("v2")
                ? history.beforeRich(address, start, route, authorization)
                : history.before(address, start, route,
                    authorization != null && authorization.startsWith("Bearer ") && authorization.length() > 7);
        } catch (RuntimeException exception) {
            historyFailed = true;
            meters.counter("gateway_shadow_feature_failures_total").increment();
        }
        String observationId = java.util.UUID.randomUUID().toString();
        if (exposeObservationId && snapshot != null) response.setHeader("X-Shadow-Observation-ID", observationId);
        boolean completedNormally = false;
        try {
            chain.doFilter(request, response);
            completedNormally = true;
        } finally {
            if (!completedNormally || request.isAsyncStarted()) {
                // The final response is not known here. Do not invent its status or train on it.
                meters.counter("gateway_shadow_incomplete_dropped_total").increment();
            } else if (snapshot != null) {
                history.after(address, start, System.nanoTime(), route, response.getStatus(), snapshot.contextKey());
                writer.record(snapshot, response.getStatus(), observationId);
            } else if (!historyFailed) {
                meters.counter("gateway_shadow_history_capacity_dropped_total").increment();
            }
        }
    }
}
