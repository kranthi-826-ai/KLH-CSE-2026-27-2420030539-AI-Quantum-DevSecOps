package com.pqc.security.monitoring.controller;

import com.pqc.security.monitoring.service.PrometheusAlertReader;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/events/operations/alerts")
public class OperationalAlertController {
    private final PrometheusAlertReader reader;
    public OperationalAlertController(PrometheusAlertReader reader) { this.reader = reader; }
    @GetMapping
    public ResponseEntity<?> alerts() {
        try {
            return ResponseEntity.ok().header("Cache-Control", "no-store").body(reader.read());
        } catch (PrometheusAlertReader.Unavailable error) {
            return ResponseEntity.status(503).header("Cache-Control", "no-store").header("Retry-After", "5")
                    .body(Map.of("status", 503, "message", "Operational alert source is unavailable; alert state is unknown"));
        }
    }
}
