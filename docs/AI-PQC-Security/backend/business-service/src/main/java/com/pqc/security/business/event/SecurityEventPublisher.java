package com.pqc.security.business.event;

import com.pqc.security.audit.SecurityEventOutbox;
import com.pqc.security.events.SecurityEvent;
import org.springframework.stereotype.Component;

@Component
public class SecurityEventPublisher {
    private final SecurityEventOutbox outbox;

    public SecurityEventPublisher(SecurityEventOutbox outbox) { this.outbox = outbox; }

    public void publish(SecurityEvent event) {
        // Do not swallow storage errors: acknowledgement requires a durable event.
        outbox.enqueue(event);
    }
}
