package com.pqc.security.monitoring.controller;

import com.pqc.security.monitoring.service.SecurityEventCollector;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class EventConflictHandler {
    @ExceptionHandler(SecurityEventCollector.EventIdentityConflict.class)
    public ResponseEntity<Map<String, Object>> conflict() {
        return ResponseEntity.status(409).header("Cache-Control", "no-store")
                .body(Map.of("status", 409, "message", "Event ID already belongs to different content"));
    }
}
