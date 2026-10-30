package com.pqc.security.audit;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import java.net.http.HttpClient;
import java.time.Clock;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.web.client.RestClient;

@Configuration(proxyBeanMethods = false)
@EnableScheduling
public class AuditOutboxConfiguration {
    @Bean AuditUnavailableHandler auditUnavailableHandler() { return new AuditUnavailableHandler(); }
    @Bean
    SecurityEventOutbox securityEventOutbox(JdbcTemplate jdbc, PlatformTransactionManager manager, MeterRegistry meters,
                                           @Value("${monitoring.outbox.max-attempts:20}") int maxAttempts) {
        var outbox = new SecurityEventOutbox(jdbc, manager, Clock.systemUTC(), maxAttempts);
        for (String status : new String[]{"PENDING", "DEAD"}) {
            Gauge.builder("audit_outbox_records", outbox, value -> value.count(status)).tag("status", status).register(meters);
        }
        Gauge.builder("audit_outbox_oldest_pending_event_age_seconds", outbox,
                SecurityEventOutbox::oldestPendingEventAgeSeconds).register(meters);
        return outbox;
    }

    @Bean OutboxOperations outboxOperations(JdbcTemplate jdbc, PlatformTransactionManager manager) {
        return new OutboxOperations(jdbc, manager, Clock.systemUTC());
    }
    @Bean OutboxOperationsController outboxOperationsController(SecurityEventOutbox outbox, OutboxOperations operations) {
        return new OutboxOperationsController(outbox, operations);
    }

    @Bean
    @ConditionalOnProperty(name = "monitoring.outbox.dispatch-enabled", havingValue = "true", matchIfMissing = true)
    OutboxDispatcher outboxDispatcher(SecurityEventOutbox outbox, DiscoveryClient discovery,
                                     @Value("${monitoring.api-key}") String apiKey) {
        var factory = new JdkClientHttpRequestFactory(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build());
        factory.setReadTimeout(Duration.ofSeconds(2));
        return new OutboxDispatcher(outbox, discovery, RestClient.builder().requestFactory(factory).build(), apiKey);
    }
}
