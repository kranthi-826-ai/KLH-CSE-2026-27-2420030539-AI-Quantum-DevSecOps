package com.pqc.security.business.client;

import com.pqc.security.business.dto.AdaptiveSecureRequest;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClientException;
import static org.junit.jupiter.api.Assertions.*;

class AdaptivePolicyClientTimeoutTests {
    @Test void acceptedButSilentDependencyHasBoundedReadWait() throws Exception {
        CountDownLatch accepted=new CountDownLatch(1), release=new CountDownLatch(1);
        try (ServerSocket server=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"))) {
            Thread peer=Thread.ofPlatform().daemon().start(() -> {
                try (var socket=server.accept()) { accepted.countDown(); release.await(); }
                catch (Exception ignored) { /* Test fixture teardown only; no request data logged. */ }
            });
            try {
                var client=new AdaptivePolicyClient("http://127.0.0.1:"+server.getLocalPort(),"synthetic-key");
                var request=new AdaptiveSecureRequest("synthetic",Map.of("dur",1),"PUBLIC",true,true,100);
                long started=System.nanoTime();
                var error=assertTimeoutPreemptively(Duration.ofSeconds(10),
                    () -> assertThrows(RestClientException.class,() -> client.evaluate(request,"timeout-fixture")));
                assertTrue(accepted.await(1,TimeUnit.SECONDS));
                Throwable cause=error;
                while (cause.getCause()!=null) cause=cause.getCause();
                assertInstanceOf(java.net.SocketTimeoutException.class,cause);
                assertTrue(Duration.ofNanos(System.nanoTime()-started).toMillis()>=4000);
            } finally { release.countDown(); server.close(); peer.join(1000); }
        }
    }
}
