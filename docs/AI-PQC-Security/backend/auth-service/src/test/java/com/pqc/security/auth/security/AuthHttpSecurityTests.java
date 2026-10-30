package com.pqc.security.auth.security;

import com.pqc.security.auth.event.SecurityEventPublisher;
import com.pqc.security.auth.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.UUID;
import java.util.regex.Pattern;
import static org.assertj.core.api.Assertions.assertThat;

/** Real HTTP and H2-backed auth flow; outbound monitoring is stubbed only. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class AuthHttpSecurityTests {
    @Value("${local.server.port}") private int port;
    @Autowired private UserRepository users;
    @MockitoBean private SecurityEventPublisher eventPublisher;
    private final HttpClient http = HttpClient.newHttpClient();

    private HttpResponse<String> post(String path, String json) throws Exception {
        return http.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + path))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json)).build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> currentUser(String token) throws Exception {
        var builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/auth/me"));
        if (token != null) builder.header("Authorization", "Bearer " + token);
        return http.send(builder.GET().build(), HttpResponse.BodyHandlers.ofString());
    }

    @Test void registrationLoginAndProtectedIdentityEnforceAuthentication() throws Exception {
        String username = "http-test-" + UUID.randomUUID().toString().substring(0, 12);
        String credentials = "{\"username\":\"" + username + "\",\"password\":\"Test-Only-Pass42!\"}";
        assertThat(currentUser(null).statusCode()).isEqualTo(401);
        assertThat(currentUser("invalid.token.value").statusCode()).isEqualTo(401);
        assertThat(post("/api/v1/auth/register", credentials).statusCode()).isEqualTo(201);
        var stored = users.findByUsername(username).orElseThrow();
        assertThat(stored.getPasswordHash()).isNotEqualTo("Test-Only-Pass42!");
        assertThat(stored.getPasswordHash()).startsWith("$2");
        assertThat(post("/api/v1/auth/register", credentials).statusCode()).isEqualTo(409);
        assertThat(post("/api/v1/auth/login", credentials.replace("Test-Only-Pass42!", "Wrong-Password42!")).statusCode()).isEqualTo(401);
        var login = post("/api/v1/auth/login", credentials);
        assertThat(login.statusCode()).isEqualTo(200);
        var matcher = Pattern.compile("\"token\"\\s*:\\s*\"([^\"]+)\"").matcher(login.body());
        assertThat(matcher.find()).isTrue();
        var identity = currentUser(matcher.group(1));
        assertThat(identity.statusCode()).isEqualTo(200);
        assertThat(identity.body()).contains(username, "ROLE_USER");
        String expired = new JwtService("test-only-jwt-secret-with-at-least-32-characters", -10000)
                .generateToken(username, "ROLE_USER");
        assertThat(currentUser(expired).statusCode()).isEqualTo(401);
    }
}
