package com.pqc.security.business.dto;

public record SecureDataResponse(
        String message,
        String username,
        String role,
        String correlationId) {
}
