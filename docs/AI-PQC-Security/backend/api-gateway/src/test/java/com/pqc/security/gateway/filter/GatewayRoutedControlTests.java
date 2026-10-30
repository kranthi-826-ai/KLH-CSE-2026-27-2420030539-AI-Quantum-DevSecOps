package com.pqc.security.gateway.filter;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;
import static org.assertj.core.api.Assertions.assertThat;

@EnabledIfSystemProperty(named = "routed.auth.url", matches = "http://127\\.0\\.0\\.1:[0-9]+")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
    "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false", "security.shadow.enabled=false",
    "security.rate-limit.api-capacity=100", "security.rate-limit.auth-capacity=4", "security.rate-limit.auth-period-seconds=3600"})
class GatewayRoutedControlTests {
    @DynamicPropertySource static void properties(DynamicPropertyRegistry p) {
        p.add("spring.cloud.gateway.server.webmvc.routes[0].id", () -> "real-auth-controls");
        p.add("spring.cloud.gateway.server.webmvc.routes[0].uri", () -> System.getProperty("routed.auth.url"));
        p.add("spring.cloud.gateway.server.webmvc.routes[0].predicates[0]", () -> "Path=/api/v1/auth/**");
    }
    @Value("${local.server.port}") private int port;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(java.time.Duration.ofSeconds(5)).build();
    private HttpRequest.Builder request(String path) {
        return HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+path)).timeout(java.time.Duration.ofSeconds(10));
    }
    private HttpResponse<String> post(String path, String body, int counter) throws Exception {
        return http.send(request(path).header("Content-Type","application/json")
            .header("X-Forwarded-For","198.51.100."+counter)
            .POST(HttpRequest.BodyPublishers.ofString(body)).build(),HttpResponse.BodyHandlers.ofString());
    }
    @Test void concurrentValidClientsWorkWhileCredentialsAndRateControlsRejectProbes() throws Exception {
        long begun = System.nanoTime();
        String username = "control-"+UUID.randomUUID().toString().substring(0,8);
        String credentials = "{\"username\":\""+username+"\",\"password\":\"Ephemeral-Control42!\"}";
        assertThat(post("/api/v1/auth/register",credentials,1).statusCode()).isEqualTo(201);
        var login = post("/api/v1/auth/login",credentials,2);
        assertThat(login.statusCode()).isEqualTo(200);
        var matcher = Pattern.compile("\"token\"\\s*:\\s*\"([^\"]+)\"").matcher(login.body());
        assertThat(matcher.find()).isTrue();
        String token = matcher.group(1);
        var pending = new ArrayList<CompletableFuture<HttpResponse<String>>>();
        for (int i=0;i<12;i++) pending.add(http.sendAsync(request("/api/v1/auth/me")
            .header("Authorization","Bearer "+token).GET().build(),HttpResponse.BodyHandlers.ofString()));
        for (var future:pending) {
            var response = future.get(15,TimeUnit.SECONDS);
            assertThat(response.statusCode()).isEqualTo(200);
            assertThat(response.body()).contains(username,"ROLE_USER");
        }
        assertThat(http.send(request("/api/v1/auth/me").header("Authorization","Bearer invalid.test.token").GET().build(),
            HttpResponse.BodyHandlers.ofString()).statusCode()).isEqualTo(401);
        assertThat(http.send(request("/api/v1/auth/me").GET().build(),HttpResponse.BodyHandlers.ofString()).statusCode()).isEqualTo(401);
        String wrong = credentials.replace("Ephemeral-Control42!","Wrong-Control42!");
        assertThat(post("/api/v1/auth/login",wrong,3).statusCode()).isEqualTo(401);
        assertThat(post("/api/v1/auth/login",wrong,4).statusCode()).isEqualTo(401);
        var limited = post("/api/v1/auth/login",wrong,5);
        assertThat(limited.statusCode()).isEqualTo(429);
        assertThat(limited.headers().firstValue("Retry-After")).isPresent();
        Path output = Path.of(System.getProperty("routed.output"),"controls.json");
        assertThat(Files.exists(output)).isFalse();
        Files.writeString(output, "{\"scope\":\"Real Gateway-to-Auth/H2 controls, not AI accuracy\",\"requests\":19,"
            +"\"concurrent_valid_requests\":12,\"concurrent_status\":200,\"missing_token_status\":401,\"invalid_token_status\":401,"
            +"\"wrong_password_statuses\":[401,401],\"rate_limit_status\":429,\"retry_after_present\":true,"
            +"\"auth_bucket_capacity\":4,\"automatic_ai_response\":false,\"elapsed_seconds\":"
            +(System.nanoTime()-begun)/1_000_000_000.+"}");
    }
}
