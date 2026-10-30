package com.pqc.security.http;

import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Pattern;

/** Bounded blocking-Servlet ingress for the project's JSON APIs, not a network firewall. */
public class RequestBoundaryFilter extends OncePerRequestFilter {
    public static final String CORRELATION_ID_HEADER = "X-Correlation-ID";
    public static final int MAX_BODY_BYTES = 262144;
    private static final Pattern SAFE_ID = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._:-]{0,79}");

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        var ids = Collections.list(request.getHeaders(CORRELATION_ID_HEADER));
        String incoming = ids.isEmpty() ? null : ids.getFirst();
        boolean invalid = ids.size() > 1 || incoming != null && !incoming.isBlank() && !SAFE_ID.matcher(incoming).matches();
        String id = incoming == null || incoming.isBlank() || invalid ? UUID.randomUUID().toString() : incoming;
        response.setHeader(CORRELATION_ID_HEADER, id);
        if (invalid) { reject(response, 400, "Invalid correlation ID"); return; }
        if (request.getContentLengthLong() > MAX_BODY_BYTES) {
            reject(response, 413, "Request body exceeds 262144 bytes"); return;
        }
        String encoding = request.getHeader("Content-Encoding");
        if (encoding != null && !encoding.equalsIgnoreCase("identity")) {
            reject(response, 415, "Encoded request bodies are not supported"); return;
        }
        byte[] body = null;
        if (!Set.of("GET", "HEAD", "OPTIONS").contains(request.getMethod())) {
            // Covers unknown-length/chunked requests without allocating an unbounded buffer.
            body = request.getInputStream().readNBytes(MAX_BODY_BYTES + 1);
            if (body.length > MAX_BODY_BYTES) {
                reject(response, 413, "Request body exceeds 262144 bytes"); return;
            }
        }
        chain.doFilter(new BoundedRequest(request, id, body), response);
    }

    private static void reject(HttpServletResponse response, int status, String message) throws IOException {
        response.setStatus(status);
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Cache-Control", "no-store");
        response.getWriter().write("{\"status\":" + status + ",\"message\":\"" + message + "\"}");
    }

    private static final class BoundedRequest extends HttpServletRequestWrapper {
        private final String correlationId;
        private final byte[] body;
        BoundedRequest(HttpServletRequest request, String correlationId, byte[] body) {
            super(request); this.correlationId = correlationId; this.body = body;
        }
        @Override public String getHeader(String name) {
            return CORRELATION_ID_HEADER.equalsIgnoreCase(name) ? correlationId : super.getHeader(name);
        }
        @Override public Enumeration<String> getHeaders(String name) {
            return CORRELATION_ID_HEADER.equalsIgnoreCase(name)
                    ? Collections.enumeration(List.of(correlationId)) : super.getHeaders(name);
        }
        @Override public Enumeration<String> getHeaderNames() {
            var names = new LinkedHashSet<>(Collections.list(super.getHeaderNames()));
            names.add(CORRELATION_ID_HEADER);
            return Collections.enumeration(names);
        }
        @Override public ServletInputStream getInputStream() throws IOException {
            if (body == null) return super.getInputStream();
            var input = new ByteArrayInputStream(body);
            return new ServletInputStream() {
                @Override public int read() { return input.read(); }
                @Override public int read(byte[] bytes, int offset, int length) { return input.read(bytes, offset, length); }
                @Override public boolean isFinished() { return input.available() == 0; }
                @Override public boolean isReady() { return true; }
                @Override public void setReadListener(ReadListener listener) {
                    throw new IllegalStateException("Nonblocking body reads are not supported by this blocking API wrapper");
                }
            };
        }
        @Override public BufferedReader getReader() throws IOException {
            return new BufferedReader(new InputStreamReader(getInputStream(),
                    getCharacterEncoding() == null ? StandardCharsets.UTF_8.name() : getCharacterEncoding()));
        }
    }
}
