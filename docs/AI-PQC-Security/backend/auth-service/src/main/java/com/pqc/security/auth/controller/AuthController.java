package com.pqc.security.auth.controller;

import com.pqc.security.auth.dto.AuthResponse;
import com.pqc.security.auth.dto.CurrentUserResponse;
import com.pqc.security.auth.dto.LoginRequest;
import com.pqc.security.auth.dto.RegisterRequest;
import com.pqc.security.auth.entity.UserEntity;
import com.pqc.security.auth.event.SecurityEventPublisher;
import com.pqc.security.auth.repository.UserRepository;
import com.pqc.security.auth.security.JwtService;
import com.pqc.security.events.SecurityEvent;
import com.pqc.security.events.SecurityEventType;
import com.pqc.security.events.SecurityOutcome;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final SecurityEventPublisher eventPublisher;

    public AuthController(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            SecurityEventPublisher eventPublisher) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.eventPublisher = eventPublisher;
    }

    @PostMapping("/register")
    @org.springframework.transaction.annotation.Transactional
    public ResponseEntity<?> register(
            @Valid @RequestBody RegisterRequest request,
            HttpServletRequest httpRequest) {
        if (userRepository.existsByUsername(request.getUsername())) {
            publishEvent(
                    SecurityEventType.REGISTRATION_REJECTED,
                    SecurityOutcome.FAILURE,
                    request.getUsername(),
                    httpRequest,
                    "Username already exists");
            return ResponseEntity
                    .status(HttpStatus.CONFLICT)
                    .body(new AuthResponse(
                            "Username already exists",
                            request.getUsername(),
                            null,
                            null));
        }

        UserEntity user = new UserEntity(
                request.getUsername(),
                passwordEncoder.encode(request.getPassword()),
                "ROLE_USER");

        userRepository.save(user);

        publishEvent(
                SecurityEventType.USER_REGISTERED,
                SecurityOutcome.SUCCESS,
                user.getUsername(),
                httpRequest,
                "User registered successfully");

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(new AuthResponse(
                        "User registered successfully",
                        user.getUsername(),
                        user.getRole(),
                        null));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {
        return userRepository.findByUsername(request.getUsername())
                .filter(user -> passwordEncoder.matches(
                        request.getPassword(),
                        user.getPasswordHash()))
                .<ResponseEntity<?>>map(user -> {
                    String token = jwtService.generateToken(
                            user.getUsername(),
                            user.getRole());

                    publishEvent(
                            SecurityEventType.LOGIN_SUCCEEDED,
                            SecurityOutcome.SUCCESS,
                            user.getUsername(),
                            httpRequest,
                            "Login successful");

                    return ResponseEntity.ok(new AuthResponse(
                            "Login successful",
                            user.getUsername(),
                            user.getRole(),
                            token));
                })
                .orElseGet(() -> {
                    publishEvent(
                            SecurityEventType.LOGIN_FAILED,
                            SecurityOutcome.FAILURE,
                            request.getUsername(),
                            httpRequest,
                            "Invalid username or password");
                    return ResponseEntity
                            .status(HttpStatus.UNAUTHORIZED)
                            .body(new AuthResponse(
                                    "Invalid username or password",
                                    request.getUsername(),
                                    null,
                                    null));
                });
    }

    @GetMapping("/me")
    public ResponseEntity<CurrentUserResponse> currentUser(Authentication authentication) {
        String role = authentication.getAuthorities().stream()
                .findFirst()
                .map(Object::toString)
                .orElse("ROLE_USER");

        return ResponseEntity.ok(new CurrentUserResponse(authentication.getName(), role));
    }

    private void publishEvent(
            SecurityEventType eventType,
            SecurityOutcome outcome,
            String username,
            HttpServletRequest request,
            String detail) {
        eventPublisher.publish(SecurityEvent.create(
                eventType,
                outcome,
                "auth-service",
                username,
                request.getHeader("X-Correlation-ID"),
                request.getMethod(),
                request.getRequestURI(),
                request.getRemoteAddr(),
                detail));
    }
}
