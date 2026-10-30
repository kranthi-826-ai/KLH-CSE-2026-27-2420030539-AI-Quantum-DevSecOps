package com.pqc.security.business.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

import static org.assertj.core.api.Assertions.assertThat;

class JwtServiceTests {

    private static final String SECRET = "test-only-jwt-secret-with-at-least-32-characters";

    @Test
    void acceptsValidAuthServiceCompatibleToken() {
        JwtService jwtService = new JwtService(SECRET);
        Instant now = Instant.now();
        String token = Jwts.builder()
                .subject("alice")
                .claim("role", "ROLE_USER")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(3600)))
                .signWith(Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8)))
                .compact();

        assertThat(jwtService.isTokenValid(token)).isTrue();
        assertThat(jwtService.parseToken(token).getSubject()).isEqualTo("alice");
    }

    @Test
    void rejectsMalformedToken() {
        assertThat(new JwtService(SECRET).isTokenValid("not-a-jwt")).isFalse();
    }
}
