package com.pqc.security.auth.dto;

public class AuthResponse {

    private final String message;
    private final String username;
    private final String role;
    private final String token;

    public AuthResponse(String message, String username, String role, String token) {
        this.message = message;
        this.username = username;
        this.role = role;
        this.token = token;
    }

    public String getMessage() {
        return message;
    }

    public String getUsername() {
        return username;
    }

    public String getRole() {
        return role;
    }
    
    public String getToken() {
        return token;
    }
}
