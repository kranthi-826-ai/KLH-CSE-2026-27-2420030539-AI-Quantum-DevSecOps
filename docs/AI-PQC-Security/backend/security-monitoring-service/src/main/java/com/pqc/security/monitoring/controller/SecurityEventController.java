package com.pqc.security.monitoring.controller;

import com.pqc.security.events.SecurityEvent;
import com.pqc.security.monitoring.dto.SecurityEventResponse;
import com.pqc.security.monitoring.repository.SecurityEventRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/events")
public class SecurityEventController {

    private final SecurityEventRepository eventRepository;
    private final com.pqc.security.monitoring.service.SecurityEventCollector collector;

    public SecurityEventController(SecurityEventRepository eventRepository, com.pqc.security.monitoring.service.SecurityEventCollector collector) {
        this.eventRepository = eventRepository;
        this.collector = collector;
    }

    @PostMapping("/internal")
    public ResponseEntity<SecurityEventResponse> collect(@RequestBody SecurityEvent event) {
        var saved = collector.collect(event);
        return ResponseEntity.status(saved.created() ? HttpStatus.CREATED : HttpStatus.OK).body(SecurityEventResponse.from(saved.event()));
    }

    @GetMapping
    public List<SecurityEventResponse> latestEvents(Authentication authentication) {
        // Scope in the database before limiting: a client-supplied username,
        // role header or UI filter must never expand the principal's access.
        boolean administrator = authentication.getAuthorities().stream()
                .anyMatch(authority -> authority.getAuthority().equals("ROLE_ADMIN"));
        var events = administrator ? eventRepository.findTop100ByOrderByOccurredAtDesc()
                : eventRepository.findTop100ByUsernameOrderByOccurredAtDesc(authentication.getName());
        return events.stream()
                .map(SecurityEventResponse::from)
                .toList();
    }
}
