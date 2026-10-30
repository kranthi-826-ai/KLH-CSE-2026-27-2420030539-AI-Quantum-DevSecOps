package com.pqc.security.auth;

import com.pqc.security.audit.*;
import com.pqc.security.events.*;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "monitoring.outbox.dispatch-enabled=false", "monitoring.outbox.operations-path=/api/v1/auth/audit-outbox",
        "spring.datasource.url=jdbc:h2:mem:auth_outbox_ops;MODE=MySQL;DB_CLOSE_DELAY=-1"})
class OutboxOperationsHttpTests {
    @Value("${local.server.port}") int port;
    @Value("${security.jwt.secret}") String secret;
    @Autowired SecurityEventOutbox outbox;
    @Autowired JdbcTemplate jdbc;

    String token(String role) {
        return Jwts.builder().subject("http-test-operator").claim("role", role)
                .expiration(new Date(System.currentTimeMillis() + 60000))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).compact();
    }
    HttpResponse<String> send(String suffix, String body, String role) throws Exception {
        var builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/auth/audit-outbox" + suffix));
        if (role != null) builder.header("Authorization", "Bearer " + token(role));
        if (body != null) builder.header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(body));
        else builder.GET();
        return HttpClient.newHttpClient().send(builder.build(), HttpResponse.BodyHandlers.ofString());
    }

    @Test void onlySignedAdministratorMayPreviewOrReplayAndMalformedRequestsAreSafe() throws Exception {
        var event = SecurityEvent.create(SecurityEventType.LOGIN_FAILED, SecurityOutcome.FAILURE,
                "auth-service", "synthetic", "replay-http", "POST", "/login", "127.0.0.1", "private-event-body");
        outbox.enqueue(event);
        outbox.dispatchOne(value -> { throw new SecurityEventOutbox.PermanentDeliveryFailure(); });
        String body = "{\"eventId\":\"" + event.eventId() + "\",\"reason\":\"RESTORED_DEPENDENCY\"}";
        assertThat(send("", null, null).statusCode()).isEqualTo(401);
        assertThat(send("", null, "ROLE_USER").statusCode()).isEqualTo(403);
        assertThat(send("/replay", body, "ROLE_USER").statusCode()).isEqualTo(403);
        assertThat(send("/replay", "{", "ROLE_USER").statusCode()).isEqualTo(403);
        var status = send("", null, "ROLE_ADMIN");
        assertThat(status.statusCode()).isEqualTo(200);
        assertThat(status.body()).contains("\"dead\":1").doesNotContain("private-event-body");
        var preview = send("/replay", body, "ROLE_ADMIN");
        assertThat(preview.statusCode()).isEqualTo(200);
        assertThat(preview.body()).contains("\"applied\":false").doesNotContain("private-event-body");
        assertThat(outbox.count("DEAD")).isEqualTo(1);
        assertThat(send("/replay", "{\"eventId\":\"not-a-uuid\"}", "ROLE_ADMIN").statusCode()).isEqualTo(400);
        var applied = send("/replay", body.replace("}", ",\"apply\":true}"), "ROLE_ADMIN");
        assertThat(applied.statusCode()).isEqualTo(200);
        assertThat(applied.body()).contains("\"applied\":true");
        assertThat(outbox.count("PENDING")).isEqualTo(1);
        assertThat(send("/replay", body.replace("}", ",\"apply\":true}"), "ROLE_ADMIN").statusCode()).isEqualTo(409);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox_replay_log WHERE event_id=?", Long.class, event.eventId().toString())).isEqualTo(1);
    }
}
