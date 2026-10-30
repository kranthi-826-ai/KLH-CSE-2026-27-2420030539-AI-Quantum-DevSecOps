package com.pqc.security.auth;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import java.net.URI;
import java.net.http.*;
import java.util.UUID;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class AuthenticationInputHttpTests {
    @Value("${local.server.port}") int port;
    HttpResponse<String> send(String path, String body) throws Exception {
        return HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + path))
                .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(body)).build(),
                HttpResponse.BodyHandlers.ofString());
    }

    @Test void malformedAndOversizedCredentialsHaveSanitizedBadRequestResponses() throws Exception {
        for (String body : new String[]{"{", "{\"username\":\"" + "x".repeat(51) + "\",\"password\":\"secret-marker\"}",
                "{\"username\":\"test\",\"password\":\"" + "p".repeat(73) + "\"}"}) {
            var response = send("/api/v1/auth/login", body);
            assertThat(response.statusCode()).isEqualTo(400);
            assertThat(response.body()).contains("Authentication request is invalid").doesNotContain("secret-marker", "Exception", "rejectedValue");
        }
    }

    @Test void bcryptLimitUsesUtf8BytesRatherThanCharacterCount() throws Exception {
        String username = "boundary_" + UUID.randomUUID().toString().substring(0, 8);
        var unicode = send("/api/v1/auth/register", "{\"username\":\"" + username + "\",\"password\":\"" + "é".repeat(37) + "\"}");
        assertThat(unicode.statusCode()).isEqualTo(400);
        assertThat(unicode.body()).doesNotContain("é", "Exception");
        var exact = send("/api/v1/auth/register", "{\"username\":\"" + username + "\",\"password\":\"" + "p".repeat(72) + "\"}");
        assertThat(exact.statusCode()).isEqualTo(201);
    }
}
