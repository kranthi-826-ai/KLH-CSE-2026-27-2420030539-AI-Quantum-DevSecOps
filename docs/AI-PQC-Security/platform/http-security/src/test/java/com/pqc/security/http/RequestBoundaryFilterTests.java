package com.pqc.security.http;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.*;
import jakarta.servlet.http.HttpServletRequest;
import java.util.concurrent.atomic.AtomicBoolean;
import static org.assertj.core.api.Assertions.assertThat;

class RequestBoundaryFilterTests {
    final RequestBoundaryFilter filter = new RequestBoundaryFilter();

    @Test void generatesMissingIdAndPreservesBoundedBodyForJsonConsumer() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/probe");
        request.setContent("{\"data\":\"hello\"}".getBytes());
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, (req, res) -> {
            var wrapped = (HttpServletRequest) req;
            assertThat(wrapped.getHeader("X-Correlation-ID")).hasSize(36);
            assertThat(wrapped.getInputStream().readAllBytes()).isEqualTo(request.getContentAsByteArray());
        });
        assertThat(response.getHeader("X-Correlation-ID")).hasSize(36);
    }

    @Test void preservesExactlyEightySafeCharacters() throws Exception {
        var request = new MockHttpServletRequest("GET", "/api/v1/probe");
        request.addHeader("X-Correlation-ID", "a".repeat(80));
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, (req, res) ->
                assertThat(((HttpServletRequest) req).getHeader("X-Correlation-ID")).isEqualTo("a".repeat(80)));
        assertThat(response.getStatus()).isEqualTo(200);
    }

    @Test void rejectsUnsafeLongAndDuplicateIdsWithoutEchoingThem() throws Exception {
        for (String id : new String[]{"x".repeat(81), "unsafe id", "unsafe\r\nid", "<script>", "abc,def"}) {
            var request = new MockHttpServletRequest("GET", "/api/v1/probe");
            request.addHeader("X-Correlation-ID", id);
            assertRejected(request, 400);
        }
        var duplicate = new MockHttpServletRequest("GET", "/api/v1/probe");
        duplicate.addHeader("X-Correlation-ID", "one");
        duplicate.addHeader("X-Correlation-ID", "two");
        assertRejected(duplicate, 400);
    }

    @Test void rejectsDeclaredOversizedBodyBeforeHandler() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/probe");
        request.setContent(new byte[RequestBoundaryFilter.MAX_BODY_BYTES + 1]);
        assertRejected(request, 413);
    }

    @Test void rejectsUnknownLengthOversizedBodyBeforeHandler() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/probe") {
            @Override public long getContentLengthLong() { return -1; }
        };
        request.setContent(new byte[RequestBoundaryFilter.MAX_BODY_BYTES + 1]);
        request.addHeader("Transfer-Encoding", "chunked");
        assertRejected(request, 413);
    }

    @Test void acceptsExactByteLimit() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/probe");
        request.setContent(new byte[RequestBoundaryFilter.MAX_BODY_BYTES]);
        filter.doFilter(request, new MockHttpServletResponse(), (req, res) ->
                assertThat(req.getInputStream().readAllBytes()).hasSize(RequestBoundaryFilter.MAX_BODY_BYTES));
    }

    @Test void rejectsEncodedBodies() throws Exception {
        var request = new MockHttpServletRequest("POST", "/api/v1/probe");
        request.addHeader("Content-Encoding", "gzip");
        assertRejected(request, 415);
    }

    void assertRejected(MockHttpServletRequest request, int status) throws Exception {
        var called = new AtomicBoolean();
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, (req, res) -> called.set(true));
        assertThat(called.get()).isFalse();
        assertThat(response.getStatus()).isEqualTo(status);
        assertThat(response.getHeader("Cache-Control")).isEqualTo("no-store");
        assertThat(response.getHeader("X-Correlation-ID")).hasSize(36);
        assertThat(response.getContentAsString()).doesNotContain("<script>", "unsafe", "password");
    }
}
