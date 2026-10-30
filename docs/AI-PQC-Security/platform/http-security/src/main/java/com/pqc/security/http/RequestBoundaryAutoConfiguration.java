package com.pqc.security.http;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.core.Ordered;

@AutoConfiguration
public class RequestBoundaryAutoConfiguration {
    @Bean
    FilterRegistrationBean<RequestBoundaryFilter> requestBoundaryFilter() {
        var registration = new FilterRegistrationBean<>(new RequestBoundaryFilter());
        registration.setName("requestBoundaryFilter");
        registration.setOrder(Ordered.HIGHEST_PRECEDENCE);
        registration.addUrlPatterns("/api/v1/*");
        return registration;
    }
}
