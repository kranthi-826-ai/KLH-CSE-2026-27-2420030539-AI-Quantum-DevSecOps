package com.pqc.security.gateway.filter;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "eureka.client.enabled=false", "spring.cloud.discovery.enabled=false"})
class OperationalAlertRouteHttpTests {
    static HttpServer upstream;
    static AtomicInteger calls = new AtomicInteger();
    static {
        try {
            upstream = HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
            upstream.createContext("/", exchange -> {
                calls.incrementAndGet();
                byte[] body = "{\"message\":\"upstream permission result\"}".getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type","application/json");
                exchange.sendResponseHeaders(403,body.length);
                try(var output=exchange.getResponseBody()){output.write(body);}
            });
            upstream.start();
        } catch(Exception error){throw new ExceptionInInitializerError(error);}
    }
    @DynamicPropertySource static void properties(DynamicPropertyRegistry values) throws Exception {
        // Spring list bindings replace rather than merge across property sources.
        // Copy the actual production route definitions, changing only the target URI.
        var production = new java.util.Properties();
        try (var input = OperationalAlertRouteHttpTests.class.getResourceAsStream("/application.properties")) {
            production.load(input);
        }
        for (String name : production.stringPropertyNames()) {
            if (name.startsWith("spring.cloud.gateway.server.webmvc.routes[")) {
                String value = production.getProperty(name);
                values.add(name, () -> value);
            }
        }
        values.add("spring.cloud.gateway.server.webmvc.routes[3].uri",()->"http://127.0.0.1:"+upstream.getAddress().getPort());
    }
    @AfterAll static void stop(){upstream.stop(0);}
    @Value("${local.server.port}") int port;
    HttpResponse<String> send(String path,boolean post)throws Exception{
        var request=HttpRequest.newBuilder(URI.create("http://127.0.0.1:"+port+path));
        if(post)request.POST(HttpRequest.BodyPublishers.ofString("{}")); else request.GET();
        return HttpClient.newHttpClient().send(request.build(),HttpResponse.BodyHandlers.ofString());
    }
    @Test void onlyTheExactReadRouteForwardsAndPreservesUpstreamPermissionStatus()throws Exception{
        var response=send("/api/v1/events/operations/alerts",false);
        assertThat(response.statusCode()).isEqualTo(403);
        assertThat(response.body()).contains("upstream permission result");
        assertThat(calls.get()).isEqualTo(1);
        assertThat(send("/api/v1/events/operations/alerts",true).statusCode()).isEqualTo(404);
        assertThat(send("/api/v1/events/internal",true).statusCode()).isEqualTo(404);
        assertThat(send("/api/v1/events/unrelated",false).statusCode()).isEqualTo(404);
        assertThat(calls.get()).isEqualTo(1);
    }
}
