package com.pqc.security.events;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

public record SecurityEvent(
        UUID eventId,
        Instant occurredAt,
        SecurityEventType eventType,
        SecurityOutcome outcome,
        String sourceService,
        String username,
        String correlationId,
        String requestMethod,
        String requestPath,
        String sourceIp,
        String detail) {

    public SecurityEvent {
        Objects.requireNonNull(eventId, "eventId is required");
        Objects.requireNonNull(occurredAt, "occurredAt is required");
        Objects.requireNonNull(eventType, "eventType is required");
        Objects.requireNonNull(outcome, "outcome is required");
        if (sourceService == null || sourceService.isBlank()) {
            throw new IllegalArgumentException("sourceService is required");
        }
    }

    public static SecurityEvent create(
            SecurityEventType eventType,
            SecurityOutcome outcome,
            String sourceService,
            String username,
            String correlationId,
            String requestMethod,
            String requestPath,
            String sourceIp,
            String detail) {
        return new SecurityEvent(
                UUID.randomUUID(),
                Instant.now(),
                eventType,
                outcome,
                sourceService,
                username,
                correlationId,
                requestMethod,
                requestPath,
                sourceIp,
                detail);
    }
}
