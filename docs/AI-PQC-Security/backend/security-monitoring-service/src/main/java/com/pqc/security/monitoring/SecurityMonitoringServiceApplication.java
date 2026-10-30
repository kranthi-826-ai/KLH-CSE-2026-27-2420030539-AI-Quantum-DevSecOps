package com.pqc.security.monitoring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@EnableDiscoveryClient
@SpringBootApplication
public class SecurityMonitoringServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(SecurityMonitoringServiceApplication.class, args);
	}

}
