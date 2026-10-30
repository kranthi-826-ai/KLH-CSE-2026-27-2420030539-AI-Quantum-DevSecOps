package com.pqc.security.gateway.filter;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class ShadowRequestHistoryTests {
    @Test void snapshotsExcludeCurrentOrFutureOutcomesAndExpire() {
        var history = new ShadowRequestHistory(2, 4);
        var first = history.before("one", 1_000_000_000L, "/api/v1/auth/login", false);
        history.after("one", 1_000_000_000L, 1_100_000_000L, "/api/v1/auth/login", 401);
        assertThat(first.features().get("prior_401_5s")).isZero();
        var next = history.before("one", 1_200_000_000L, "/api/v1/auth/me", true);
        assertThat(next.features().get("prior_failed_login_5s")).isEqualTo(1.);
        assertThat(next.features().get("prior_requests_1s")).isEqualTo(1.);
        assertThat(next.features().get("seconds_since_previous_start")).isEqualTo(.2);
        var other = history.before("two", 1_200_000_000L, "/api/v1/auth/me", true);
        assertThat(other.features().get("prior_401_5s")).isZero();
        assertThat(other.peerId()).isNotEqualTo(first.peerId());
        assertThat(history.before("one", 7_000_000_000L, "/api/v1/auth/me", true).features().get("prior_401_5s")).isZero();
    }
    @Test void historyAndPeerMemoryAreBoundedWithoutRejectingTraffic() {
        var history = new ShadowRequestHistory(1, 2);
        history.before("one", 1, "/api/v1/auth/me", true);
        for (int i = 0; i < 5; i++) history.after("one", i + 2, i + 3, "/api/v1/auth/me", 401);
        assertThat(history.before("one", 10, "/api/v1/auth/me", true).features().get("prior_401_5s")).isEqualTo(2.);
        assertThat(history.before("two", 11, "/api/v1/auth/me", true)).isNull();
        assertThat(history.before("two", 70_000_000_000L, "/api/v1/auth/me", true)).isNotNull();
    }
    @Test void outOfOrderConcurrentCompletionsDoNotMoveTheClockBack() {
        var history = new ShadowRequestHistory(1, 4);
        history.before("one", 1, "/api/v1/auth/me", true);
        history.after("one", 2_000_000_000L, 3_000_000_000L, "/api/v1/auth/me", 200);
        history.after("one", 1_000_000_000L, 4_000_000_000L, "/api/v1/auth/login", 401);
        var snapshot = history.before("one", 4_500_000_000L, "/api/v1/auth/me", true);
        assertThat(snapshot.features().get("seconds_since_previous_start")).isEqualTo(2.5);
        assertThat(snapshot.features().get("prior_401_5s")).isEqualTo(1.);
    }
}
