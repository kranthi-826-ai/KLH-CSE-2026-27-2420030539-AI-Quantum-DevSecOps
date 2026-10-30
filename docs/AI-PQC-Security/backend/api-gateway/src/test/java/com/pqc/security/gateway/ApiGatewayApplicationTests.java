package com.pqc.security.gateway;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import com.pqc.security.gateway.filter.GatewayShadowFilter;
import com.pqc.security.gateway.filter.ShadowObservationWriter;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(properties = "eureka.client.enabled=false")
class ApiGatewayApplicationTests {

    @Autowired private ApplicationContext context;

	@Test
	void contextLoads() {
	    assertThat(context.getBeansOfType(GatewayShadowFilter.class)).isEmpty();
	    assertThat(context.getBeansOfType(ShadowObservationWriter.class)).isEmpty();
	}

}
