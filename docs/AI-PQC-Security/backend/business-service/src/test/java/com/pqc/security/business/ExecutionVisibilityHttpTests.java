package com.pqc.security.business;

import com.pqc.security.business.entity.CryptoExecutionEntity;
import com.pqc.security.business.repository.CryptoExecutionRepository;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ExecutionVisibilityHttpTests {
    @Value("${local.server.port}") int port;
    @Value("${security.jwt.secret}") String secret;
    @Autowired CryptoExecutionRepository repository;

    String token(String name, String role) {
        return Jwts.builder().subject(name).claim("role", role)
                .expiration(new Date(System.currentTimeMillis() + 60000))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).compact();
    }

    HttpResponse<String> get(String token, String query) throws Exception {
        var request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/business/executions" + query))
                .header("X-Role", "ROLE_ADMIN").header("X-Username", "another-user");
        if (token != null) request.header("Authorization", "Bearer " + token);
        return HttpClient.newHttpClient().send(request.GET().build(), HttpResponse.BodyHandlers.ofString());
    }

    @Test void signedIdentityScopesRowsAndOnlySignedAdminGetsGlobalView() throws Exception {
        String alice = "alice_" + UUID.randomUUID().toString().substring(0, 8);
        String bob = "bob_" + UUID.randomUUID().toString().substring(0, 8);
        for (String name : new String[]{alice, bob}) repository.saveAndFlush(new CryptoExecutionEntity(
                UUID.randomUUID().toString(), Instant.now(), "visibility-test", name, "a".repeat(64)));
        var own = get(token(alice, "ROLE_USER"), "?username=" + bob + "&role=ROLE_ADMIN");
        assertThat(own.statusCode()).isEqualTo(200);
        assertThat(own.body()).contains(alice).doesNotContain(bob);
        var other = get(token(bob, "ROLE_USER"), "");
        assertThat(other.body()).contains(bob).doesNotContain(alice);
        var empty = get(token("unrelated_" + UUID.randomUUID(), "ROLE_USER"), "");
        assertThat(empty.body()).isEqualTo("[]");
        var admin = get(token("security-operator", "ROLE_ADMIN"), "");
        assertThat(admin.statusCode()).isEqualTo(200);
        assertThat(admin.body()).contains(alice, bob);
        assertThat(get(null, "").statusCode()).isEqualTo(401);
    }
}
