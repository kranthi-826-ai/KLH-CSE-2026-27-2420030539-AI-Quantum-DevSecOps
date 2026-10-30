package com.pqc.security.auth.security;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class JwtServiceTests {

    private static final String SECRET = "test-only-jwt-secret-with-at-least-32-characters";

    @Test
    void generatedTokenContainsExpectedIdentityAndRole() {
        JwtService jwtService = new JwtService(SECRET, 3_600_000);

        String token = jwtService.generateToken("alice", "ROLE_USER");

        assertThat(jwtService.isTokenValid(token)).isTrue();
        assertThat(jwtService.extractUsername(token)).isEqualTo("alice");
        assertThat(jwtService.extractRole(token)).isEqualTo("ROLE_USER");
    }

    @Test
    void tokenWithInvalidSignatureIsRejected() {
        JwtService issuer = new JwtService(SECRET, 3_600_000);
        JwtService verifier = new JwtService(
                "different-test-secret-with-at-least-32-characters",
                3_600_000);

        String token = issuer.generateToken("alice", "ROLE_USER");

        assertThat(verifier.isTokenValid(token)).isFalse();
    }

    @Test
    void expiredTokenIsRejected() {
        JwtService jwtService = new JwtService(SECRET, -1);

        String token = jwtService.generateToken("alice", "ROLE_USER");

        assertThat(jwtService.isTokenValid(token)).isFalse();
    }
}
