package com.pqc.security.monitoring.service;

import com.pqc.security.events.SecurityEvent;
import com.pqc.security.monitoring.entity.SecurityEventEntity;
import com.pqc.security.monitoring.repository.SecurityEventRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class SecurityEventCollector {
    private final SecurityEventRepository repository;
    private final TransactionTemplate transactions;

    public SecurityEventCollector(SecurityEventRepository repository, PlatformTransactionManager manager) {
        this.repository = repository;
        this.transactions = new TransactionTemplate(manager);
    }

    public Collected collect(SecurityEvent event) {
        var candidate = new SecurityEventEntity(event);
        var existing = repository.findByEventId(event.eventId().toString());
        if (existing.isPresent()) return sameOrConflict(existing.get(), candidate);
        try {
            var saved = transactions.execute(ignored -> repository.saveAndFlush(candidate));
            return new Collected(saved, true);
        } catch (DataIntegrityViolationException race) {
            // Read only after the failed insert transaction has fully rolled back.
            return repository.findByEventId(event.eventId().toString())
                    .map(found -> sameOrConflict(found, candidate)).orElseThrow(() -> race);
        }
    }

    private Collected sameOrConflict(SecurityEventEntity existing, SecurityEventEntity supplied) {
        if (!existing.asEvent().equals(supplied.asEvent())) {
            throw new EventIdentityConflict();
        }
        return new Collected(existing, false);
    }

    public record Collected(SecurityEventEntity event, boolean created) { }
    public static class EventIdentityConflict extends RuntimeException { }
}
