package com.pqc.security.monitoring.dto;

import com.pqc.security.monitoring.entity.SecurityEventEntity;

import java.time.Instant;

public record SecurityEventResponse(
        String eventId,
        Instant occurredAt,
        String eventType,
        String outcome,
        String sourceService,
        String username,
        String correlationId,
        String requestMethod,
        String requestPath,
        String sourceIp,
        String detail) {

    public static SecurityEventResponse from(SecurityEventEntity entity) {
        return new SecurityEventResponse(
                entity.getEventId(),
                entity.getOccurredAt(),
                entity.getEventType(),
                entity.getOutcome(),
                entity.getSourceService(),
                entity.getUsername(),
                entity.getCorrelationId(),
                entity.getRequestMethod(),
                entity.getRequestPath(),
                entity.getSourceIp(),
                entity.getDetail());
    }
}
