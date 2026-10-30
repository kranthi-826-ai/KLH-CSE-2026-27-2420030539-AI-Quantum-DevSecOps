package com.pqc.security.business.service;

import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.event.SecurityEventPublisher;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import com.pqc.security.events.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ExecutionAuditWriter {
    private final CryptoExecutionRepository repository;
    private final SecurityEventPublisher events;
    public ExecutionAuditWriter(CryptoExecutionRepository repository, SecurityEventPublisher events) {
        this.repository = repository; this.events = events;
    }

    @Transactional
    public void save(CryptoExecutionEntity audit, String sourceIp) {
        repository.save(audit);
        if ("STARTED".equals(audit.getOutcome())) return;
        boolean success = "SUCCESS".equals(audit.getOutcome()) && audit.isRoundTripVerified();
        events.publish(SecurityEvent.create(success ? SecurityEventType.API_ACCESS_GRANTED : SecurityEventType.API_ACCESS_DENIED,
                success ? SecurityOutcome.SUCCESS : SecurityOutcome.FAILURE, "business-service", audit.getUsername(),
                audit.getCorrelationId(), "POST", "/api/v1/business/adaptive-secure-data", sourceIp,
                success ? "Adaptive protection applied: " + audit.getSelectedMode() : "Adaptive security execution failed; inspect the execution audit"));
    }
}
