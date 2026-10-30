package com.pqc.security.business.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.RestClientException;
import com.pqc.security.business.security.PublicFailureMessages;

import java.security.GeneralSecurityException;
import java.time.Instant;
import java.util.Map;

@RestControllerAdvice
public class AdaptiveSecurityExceptionHandler {

    @ExceptionHandler({RestClientException.class})
    public ResponseEntity<Map<String, Object>> dependencyFailure(RuntimeException exception) {
        return error(HttpStatus.BAD_GATEWAY, PublicFailureMessages.describe(exception));
    }

    @ExceptionHandler({GeneralSecurityException.class, IllegalArgumentException.class})
    public ResponseEntity<Map<String, Object>> cryptoFailure(Exception exception) {
        return error(HttpStatus.UNPROCESSABLE_ENTITY, PublicFailureMessages.describe(exception));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> invalidRequest(MethodArgumentNotValidException exception) {
        return error(HttpStatus.BAD_REQUEST, "Adaptive security request is invalid");
    }

    private static ResponseEntity<Map<String, Object>> error(HttpStatus status, String message) {
        return ResponseEntity.status(status).body(Map.of(
                "timestamp", Instant.now().toString(),
                "status", status.value(),
                "error", status.getReasonPhrase(),
                "message", message == null ? "Adaptive security operation failed" : message));
    }
}
