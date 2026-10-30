package com.pqc.security.business.controller;

import com.pqc.security.business.dto.SecureDataResponse;
import com.pqc.security.business.dto.AdaptiveSecureRequest;
import com.pqc.security.business.dto.AdaptiveSecureResponse;
import com.pqc.security.business.dto.CryptoExecutionResponse;
import com.pqc.security.business.event.SecurityEventPublisher;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import com.pqc.security.business.service.AdaptiveSecurityService;
import com.pqc.security.events.SecurityEvent;
import com.pqc.security.events.SecurityEventType;
import com.pqc.security.events.SecurityOutcome;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/business")
public class BusinessController {

    private final SecurityEventPublisher eventPublisher;
    private final AdaptiveSecurityService adaptiveSecurityService;
    private final CryptoExecutionRepository executionRepository;

    public BusinessController(SecurityEventPublisher eventPublisher,
                              AdaptiveSecurityService adaptiveSecurityService,
                              CryptoExecutionRepository executionRepository) {
        this.eventPublisher = eventPublisher;
        this.adaptiveSecurityService = adaptiveSecurityService;
        this.executionRepository = executionRepository;
    }

    @GetMapping("/executions")
    public List<CryptoExecutionResponse> latestExecutions(Authentication authentication) {
        boolean administrator = authentication.getAuthorities().stream()
                .anyMatch(authority -> authority.getAuthority().equals("ROLE_ADMIN"));
        var executions = administrator ? executionRepository.findTop100ByOrderByExecutedAtDesc()
                : executionRepository.findTop100ByUsernameOrderByExecutedAtDesc(authentication.getName());
        return executions.stream()
                .map(CryptoExecutionResponse::from)
                .toList();
    }

    @GetMapping("/secure-data")
    public ResponseEntity<SecureDataResponse> secureData(
            Authentication authentication,
            HttpServletRequest request) {
        String role = authentication.getAuthorities().stream()
                .findFirst()
                .map(Object::toString)
                .orElse("ROLE_USER");
        String correlationId = request.getHeader("X-Correlation-ID");

        eventPublisher.publish(SecurityEvent.create(
                SecurityEventType.API_ACCESS_GRANTED,
                SecurityOutcome.SUCCESS,
                "business-service",
                authentication.getName(),
                correlationId,
                request.getMethod(),
                request.getRequestURI(),
                request.getRemoteAddr(),
                "Protected business API accessed"));

        return ResponseEntity.ok(new SecureDataResponse(
                "Protected business data accessed successfully",
                authentication.getName(),
                role,
                correlationId));
    }

    @PostMapping("/adaptive-secure-data")
    public ResponseEntity<AdaptiveSecureResponse> adaptiveSecureData(
            @Valid @RequestBody AdaptiveSecureRequest secureRequest,
            @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId,
            Authentication authentication,
            HttpServletRequest servletRequest) throws java.security.GeneralSecurityException {
        AdaptiveSecureResponse response = adaptiveSecurityService.protect(
                secureRequest, authentication.getName(), correlationId, servletRequest.getRemoteAddr());
        return ResponseEntity.ok(response);
    }
}
