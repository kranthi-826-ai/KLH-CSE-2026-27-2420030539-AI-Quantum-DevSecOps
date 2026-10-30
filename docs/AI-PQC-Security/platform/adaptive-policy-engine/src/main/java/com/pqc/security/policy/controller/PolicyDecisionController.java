package com.pqc.security.policy.controller;

import com.pqc.security.policy.dto.PolicyDecisionRequest;
import com.pqc.security.policy.dto.PolicyDecisionResponse;
import com.pqc.security.policy.dto.NetworkPolicyRequest;
import com.pqc.security.policy.service.PolicyDecisionService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/policies/decisions")
public class PolicyDecisionController {

    private final PolicyDecisionService service;

    public PolicyDecisionController(PolicyDecisionService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<PolicyDecisionResponse> decide(
            @Valid @RequestBody PolicyDecisionRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.decide(request));
    }

    @GetMapping
    public List<PolicyDecisionResponse> latest() {
        return service.latest();
    }

    @PostMapping("/evaluate-network")
    public ResponseEntity<PolicyDecisionResponse> evaluateNetwork(
            @Valid @RequestBody NetworkPolicyRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.evaluateNetwork(request));
    }
}
