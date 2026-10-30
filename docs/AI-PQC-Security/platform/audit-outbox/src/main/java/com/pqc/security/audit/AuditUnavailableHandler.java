package com.pqc.security.audit;

import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class AuditUnavailableHandler {
    @ExceptionHandler(AuditUnavailableException.class)
    public ResponseEntity<Map<String, Object>> unavailable() {
        return ResponseEntity.status(503).header("Retry-After", "3").header("Cache-Control", "no-store")
                .body(Map.of("status", 503, "message", "Durable audit storage is unavailable. The operation was not acknowledged."));
    }
}
