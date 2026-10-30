package com.pqc.security.gateway.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.filter.OncePerRequestFilter;

/** Preserve fail-closed availability semantics when a functional route cannot find its backend. */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 5)
public class DependencyFailureFilter extends OncePerRequestFilter {
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !request.getRequestURI().startsWith(request.getContextPath() + "/api/v1/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                   FilterChain chain) throws ServletException, IOException {
        try {
            chain.doFilter(request, response);
        } catch (ServletException | RuntimeException error) {
            if (response.isCommitted() || !isUnavailable(error)) throw error;
            response.resetBuffer();
            response.setStatus(503);
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.setHeader("Cache-Control", "no-store");
            response.setHeader("Retry-After", "2");
            response.getWriter().write("{\"status\":503,\"error\":\"Service Unavailable\",\"message\":\"A required backend service is unavailable. Retry shortly.\"}");
        }
    }

    private static boolean isUnavailable(Throwable error) {
        for (int depth = 0; error != null && depth < 12; depth++, error = error.getCause()) {
            if (error instanceof ResourceAccessException) return true;
            if (error instanceof HttpServerErrorException upstream && upstream.getStatusCode().value() == 503) return true;
        }
        return false;
    }
}
