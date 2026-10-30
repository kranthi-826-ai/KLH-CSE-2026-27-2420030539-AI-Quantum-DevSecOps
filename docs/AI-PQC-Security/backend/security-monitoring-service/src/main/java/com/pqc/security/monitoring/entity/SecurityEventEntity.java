package com.pqc.security.monitoring.entity;

import com.pqc.security.events.SecurityEvent;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "security_events")
public class SecurityEventEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 36)
    private String eventId;

    @Column(nullable = false)
    private Instant occurredAt;

    @Column(nullable = false, length = 50)
    private String eventType;

    @Column(nullable = false, length = 20)
    private String outcome;

    @Column(nullable = false, length = 80)
    private String sourceService;

    @Column(length = 50)
    private String username;

    @Column(length = 80)
    private String correlationId;

    @Column(length = 10)
    private String requestMethod;

    @Column(length = 255)
    private String requestPath;

    @Column(length = 64)
    private String sourceIp;

    @Column(length = 500)
    private String detail;

    protected SecurityEventEntity() {
    }

    public SecurityEventEntity(SecurityEvent event) {
        this.eventId = event.eventId().toString();
        this.occurredAt = event.occurredAt().truncatedTo(java.time.temporal.ChronoUnit.MICROS);
        this.eventType = event.eventType().name();
        this.outcome = event.outcome().name();
        this.sourceService = event.sourceService();
        this.username = event.username();
        this.correlationId = event.correlationId();
        this.requestMethod = event.requestMethod();
        this.requestPath = event.requestPath();
        this.sourceIp = event.sourceIp();
        this.detail = event.detail();
    }

    public Long getId() {
        return id;
    }

    public SecurityEvent asEvent() {
        return new SecurityEvent(java.util.UUID.fromString(eventId), occurredAt,
                com.pqc.security.events.SecurityEventType.valueOf(eventType),
                com.pqc.security.events.SecurityOutcome.valueOf(outcome), sourceService,
                username, correlationId, requestMethod, requestPath, sourceIp, detail);
    }

    public String getEventId() {
        return eventId;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }

    public String getEventType() {
        return eventType;
    }

    public String getOutcome() {
        return outcome;
    }

    public String getSourceService() {
        return sourceService;
    }

    public String getUsername() {
        return username;
    }

    public String getCorrelationId() {
        return correlationId;
    }

    public String getRequestMethod() {
        return requestMethod;
    }

    public String getRequestPath() {
        return requestPath;
    }

    public String getSourceIp() {
        return sourceIp;
    }

    public String getDetail() {
        return detail;
    }
}
