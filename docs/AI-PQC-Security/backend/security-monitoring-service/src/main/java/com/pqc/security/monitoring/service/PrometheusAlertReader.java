package com.pqc.security.monitoring.service;

import java.net.http.HttpClient;
import java.time.*;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import tools.jackson.databind.json.JsonMapper;

@Service
public class PrometheusAlertReader {
    private static final Set<String> NAMES = Set.of("AuditOutboxDeadEvents", "AuditOutboxOldPendingEvents",
            "AuditProducerUnavailable", "AuditOutboxMetricsUnavailable",
            "AdaptiveAuditWriteFailure", "AdaptiveAuditMetricUnavailable");
    private final RestClient client;
    private final JsonMapper mapper = JsonMapper.builder().build();
    public PrometheusAlertReader(@Value("${monitoring.prometheus.url:http://127.0.0.1:9090}") String url) {
        var factory = new JdkClientHttpRequestFactory(HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build());
        factory.setReadTimeout(Duration.ofSeconds(2));
        client = RestClient.builder().baseUrl(url).requestFactory(factory).build();
    }
    public record Alert(String name, String state, String application, String instance,
                        String severity, String summary, String description, String activeAt) { }
    public record Snapshot(String source, String retrievedAt, List<Alert> alerts) { }

    public Snapshot read() {
        try {
            Map<?, ?> root = client.get().uri("/api/v1/alerts").exchange((request, response) -> {
                if (!response.getStatusCode().is2xxSuccessful()) throw new Unavailable();
                byte[] body = response.getBody().readNBytes(1_048_577);
                if (body.length > 1_048_576) throw new Unavailable();
                return mapper.readValue(body, Map.class);
            });
            if (root == null || !"success".equals(root.get("status")) || !(root.get("data") instanceof Map<?, ?> data)
                    || !(data.get("alerts") instanceof List<?> rows) || rows.size() > 1000) throw new Unavailable();
            var alerts = new ArrayList<Alert>();
            for (Object row : rows) {
                if (!(row instanceof Map<?, ?> item) || !(item.get("labels") instanceof Map<?, ?> labels)) throw new Unavailable();
                String name = text(labels, "alertname", 100);
                if (!NAMES.contains(name)) continue;
                String state = text(item, "state", 16);
                if (!Set.of("pending", "firing").contains(state)) throw new Unavailable();
                var annotations = item.get("annotations") instanceof Map<?, ?> value ? value : Map.of();
                alerts.add(new Alert(name, state, text(labels, "application", 100), text(labels, "instance", 256),
                        text(labels, "severity", 32), text(annotations, "summary", 256), text(annotations, "description", 1000),
                        text(item, "activeAt", 100)));
            }
            alerts.sort(Comparator.comparing(Alert::name).thenComparing(Alert::instance));
            return new Snapshot("Prometheus", Instant.now().toString(), List.copyOf(alerts));
        } catch (RuntimeException error) {
            throw new Unavailable(); // No upstream URL, response body, credentials or exception text in the API.
        }
    }
    private static String text(Map<?, ?> map, String key, int max) {
        Object value = map.get(key);
        if (value == null) return "";
        if (!(value instanceof String text) || text.length() > max) throw new Unavailable();
        return text;
    }
    public static class Unavailable extends RuntimeException { }
}
