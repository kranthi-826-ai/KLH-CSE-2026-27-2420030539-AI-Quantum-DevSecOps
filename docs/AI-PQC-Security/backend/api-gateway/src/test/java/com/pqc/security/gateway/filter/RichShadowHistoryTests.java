package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.assertj.core.api.Assertions.assertThat;

class RichShadowHistoryTests {
    @TempDir Path directory;
    @Test void credentialContextsDoNotEraseAggregateHistoryOrPoisonOtherCredentials() {
        var history = new ShadowRequestHistory(2,32);
        var a = history.beforeRich("peer",1_000_000_000L,"/api/v1/auth/me","Bearer secret-A");
        history.after("peer",1_000_000_000L,1_100_000_000L,"/api/v1/auth/me",401,a.contextKey());
        var b = history.beforeRich("peer",1_200_000_000L,"/api/v1/auth/me","Bearer secret-B");
        assertThat(b.features().get("prior_401_5s")).isEqualTo(1.);
        assertThat(b.features().get("context_prior_401_5s")).isZero();
        assertThat(b.features().get("context_is_new")).isEqualTo(1.);
        history.after("peer",1_200_000_000L,1_300_000_000L,"/api/v1/auth/me",200,b.contextKey());
        var again = history.beforeRich("peer",1_400_000_000L,"/api/v1/auth/me","Bearer secret-A");
        assertThat(again.contextKey()).isEqualTo(a.contextKey()).doesNotContain("secret-A");
        assertThat(again.features().get("context_prior_401_5s")).isEqualTo(1.);
        assertThat(again.features().get("context_consecutive_401")).isEqualTo(1.);
        assertThat(again.features().get("peer_last_was_401")).isZero();
        assertThat(again.features()).hasSize(24);
        assertThat(new ShadowRequestHistory(2,32).beforeRich("peer",1,"/api/v1/auth/me","Bearer secret-A").contextKey())
            .isNotEqualTo(a.contextKey());
    }
    @Test void credentialRotationKeepsAggregateFailureAndChurnEvidence() {
        var history = new ShadowRequestHistory(1,32);
        for(int i=0;i<3;i++) {
            var snapshot = history.beforeRich("peer",10+i*10,"/api/v1/auth/me","Bearer rotation-"+i);
            history.after("peer",10+i*10,11+i*10,"/api/v1/auth/me",401,snapshot.contextKey());
        }
        var next = history.beforeRich("peer",50,"/api/v1/auth/me","Bearer another-new-token");
        assertThat(next.features().get("context_prior_401_5s")).isZero();
        assertThat(next.features().get("peer_consecutive_401")).isEqualTo(3.);
        assertThat(next.features().get("unique_bearer_contexts_5s")).isEqualTo(3.);
        assertThat(next.features().get("prior_401_5s")).isEqualTo(3.);
    }
    @Test void richOutputNeverExportsCredentialValuesOrContextDigests() throws Exception {
        var snapshot = new ShadowRequestHistory(1,4).beforeRich("peer",1,"/api/v1/auth/me","Bearer highly-private-token");
        Path output=directory.resolve("rich.jsonl");
        try(var writer=new ShadowObservationWriter(output.toString(),new SimpleMeterRegistry())) { writer.record(snapshot,401); }
        assertThat(Files.readString(output)).contains("gateway-peer-shadow-v2").doesNotContain("highly-private-token",snapshot.contextKey());
    }
}
