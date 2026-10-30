package com.pqc.security.business.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pqc.security.business.event.SecurityEventPublisher;
import com.pqc.security.events.SecurityEvent;
import com.pqc.security.events.SecurityEventType;
import com.pqc.security.events.SecurityOutcome;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@Component
public class RestAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper;
    private final SecurityEventPublisher eventPublisher;

    public RestAuthenticationEntryPoint(ObjectMapper objectMapper, SecurityEventPublisher eventPublisher) {
        this.objectMapper = objectMapper;
        this.eventPublisher = eventPublisher;
    }

    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException exception) throws IOException {

        eventPublisher.publish(SecurityEvent.create(
                SecurityEventType.API_ACCESS_DENIED,
                SecurityOutcome.DENIED,
                "business-service",
                null,
                request.getHeader("X-Correlation-ID"),
                request.getMethod(),
                request.getRequestURI(),
                request.getRemoteAddr(),
                "Missing or invalid JWT"));

        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("timestamp", Instant.now().toString());
        body.put("status", HttpServletResponse.SC_UNAUTHORIZED);
        body.put("error", "Unauthorized");
        body.put("message", "A valid bearer token is required");
        body.put("path", request.getRequestURI());
        objectMapper.writeValue(response.getOutputStream(), body);
    }
}
