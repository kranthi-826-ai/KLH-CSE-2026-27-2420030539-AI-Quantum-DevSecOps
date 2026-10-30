package com.pqc.security.auth.security;

import com.pqc.security.audit.SecurityEventOutbox;
import com.pqc.security.auth.repository.UserRepository;
import java.net.URI;
import java.net.http.*;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "monitoring.outbox.dispatch-enabled=false", "spring.datasource.url=jdbc:h2:mem:auth_outbox;MODE=MySQL;DB_CLOSE_DELAY=-1"})
class AuthOutboxTransactionTests {
    @Value("${local.server.port}") int port;
    @Autowired UserRepository users;
    @Autowired JdbcTemplate jdbc;
    @MockitoSpyBean SecurityEventOutbox outbox;

    int register(String username) throws Exception {
        return HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/v1/auth/register"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{\"username\":\"" + username + "\",\"password\":\"Test-only-Password42!\"}"))
                .build(), HttpResponse.BodyHandlers.discarding()).statusCode();
    }

    @Test void registrationAndAuditCommitTogetherWithoutMonitoring() throws Exception {
        String username = "outbox-" + UUID.randomUUID().toString().substring(0, 12);
        assertThat(register(username)).isEqualTo(201);
        assertThat(users.existsByUsername(username)).isTrue();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE username=? AND status='PENDING'", Long.class, username)).isEqualTo(1);
    }

    @Test void auditStorageFailureRollsBackUserCreation() throws Exception {
        String username = "rollback-" + UUID.randomUUID().toString().substring(0, 12);
        doThrow(new com.pqc.security.audit.AuditUnavailableException(new IllegalStateException("test-only persistence failure"))).when(outbox).enqueue(any());
        try {
            assertThat(register(username)).isEqualTo(503);
            assertThat(users.existsByUsername(username)).isFalse();
            assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_outbox WHERE username=?", Long.class, username)).isZero();
        } finally { doCallRealMethod().when(outbox).enqueue(any()); }
    }
}
