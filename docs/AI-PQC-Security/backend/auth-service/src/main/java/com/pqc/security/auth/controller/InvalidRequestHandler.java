package com.pqc.security.auth.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestControllerAdvice
public class InvalidRequestHandler {
    @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<Map<String, Object>> invalid(Exception ignored) {
        // Never serialize BindingResult/rejected values: those may contain passwords.
        return ResponseEntity.badRequest().header("Cache-Control", "no-store")
                .body(Map.of("status", 400, "message", "Authentication request is invalid"));
    }
}
