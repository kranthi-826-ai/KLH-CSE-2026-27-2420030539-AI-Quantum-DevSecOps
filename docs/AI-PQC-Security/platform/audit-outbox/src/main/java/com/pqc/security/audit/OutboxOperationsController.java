package com.pqc.security.audit;

import java.util.Map;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("${monitoring.outbox.operations-path:/api/v1/audit-outbox}")
public class OutboxOperationsController {
    private final SecurityEventOutbox outbox;
    private final OutboxOperations operations;
    public OutboxOperationsController(SecurityEventOutbox outbox, OutboxOperations operations) {
        this.outbox = outbox; this.operations = operations;
    }

    private static boolean administrator(Authentication auth) {
        return auth != null && auth.isAuthenticated() && auth.getAuthorities().stream()
                .anyMatch(value -> value.getAuthority().equals("ROLE_ADMIN"));
    }
    private static ResponseEntity<?> result(int status, Object body) {
        return ResponseEntity.status(status).header("Cache-Control", "no-store").body(body);
    }

    @GetMapping
    public ResponseEntity<?> status(Authentication auth) {
        if (!administrator(auth)) return result(403, Map.of("status", 403, "message", "Administrator access required"));
        return result(200, Map.of("pending", outbox.count("PENDING"), "dead", outbox.count("DEAD"),
                "delivered", outbox.count("DELIVERED"), "oldestPendingEventAgeSeconds", outbox.oldestPendingEventAgeSeconds(),
                "recentDead", operations.recentDead()));
    }

    public record ReplayRequest(UUID eventId, String reason, Boolean apply) { }
    @ExceptionHandler(org.springframework.http.converter.HttpMessageNotReadableException.class)
    public ResponseEntity<?> malformedReplay() {
        return result(400, Map.of("status", 400, "message", "Invalid replay request"));
    }
    @ExceptionHandler(org.springframework.dao.DataAccessException.class)
    public ResponseEntity<?> storageUnavailable() {
        return result(503, Map.of("status", 503, "message", "Outbox operation unavailable"));
    }
    @PostMapping("/replay")
    public ResponseEntity<?> replay(@RequestBody ReplayRequest request, Authentication auth) {
        if (!administrator(auth)) return result(403, Map.of("status", 403, "message", "Administrator access required"));
        try {
            return result(200, operations.replay(request.eventId(), auth.getName(), request.reason(), Boolean.TRUE.equals(request.apply())));
        } catch (OutboxOperations.MissingEvent error) {
            return result(404, Map.of("status", 404, "message", "Outbox event not found"));
        } catch (OutboxOperations.IneligibleState error) {
            return result(409, Map.of("status", 409, "message", "Only DEAD events may be replayed"));
        } catch (IllegalArgumentException error) {
            return result(400, Map.of("status", 400, "message", "Invalid replay request"));
        }
    }
}
