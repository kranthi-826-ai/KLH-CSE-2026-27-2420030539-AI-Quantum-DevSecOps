package com.pqc.security.audit;

import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.HttpClientErrorException;

public class OutboxDispatcher {
    private final SecurityEventOutbox outbox;
    private final DiscoveryClient discovery;
    private final RestClient client;
    private final String apiKey;
    private final AtomicBoolean running = new AtomicBoolean();

    public OutboxDispatcher(SecurityEventOutbox outbox, DiscoveryClient discovery, RestClient client, String apiKey) {
        this.outbox = outbox; this.discovery = discovery; this.client = client; this.apiKey = apiKey;
    }

    @Scheduled(fixedDelayString = "${monitoring.outbox.interval-ms:2000}")
    public void flush() {
        if (!running.compareAndSet(false, true)) return;
        try {
            long deadline = System.nanoTime() + 5_000_000_000L;
            for (int count = 0; count < 10 && System.nanoTime() < deadline; count++) {
                boolean processed = outbox.dispatchOne(event -> {
                    var instances = discovery.getInstances("security-monitoring-service");
                    if (instances.isEmpty()) throw new IllegalStateException("Monitoring unavailable");
                    try {
                        var receipt = client.post().uri(instances.getFirst().getUri().resolve("/api/v1/events/internal"))
                                .header("X-Internal-API-Key", apiKey).contentType(org.springframework.http.MediaType.APPLICATION_JSON)
                                .body(event).retrieve().toEntity(java.util.Map.class);
                        int status = receipt.getStatusCode().value();
                        if ((status != 200 && status != 201) || receipt.getBody() == null
                                || !event.eventId().toString().equals(receipt.getBody().get("eventId"))) {
                            throw new IllegalStateException("No matching durable acknowledgement");
                        }
                    } catch (HttpClientErrorException error) {
                        int status = error.getStatusCode().value();
                        if (status == 400 || status == 409 || status == 422) throw new SecurityEventOutbox.PermanentDeliveryFailure();
                        throw error;
                    }
                });
                if (!processed) break;
            }
        } finally { running.set(false); }
    }
}
