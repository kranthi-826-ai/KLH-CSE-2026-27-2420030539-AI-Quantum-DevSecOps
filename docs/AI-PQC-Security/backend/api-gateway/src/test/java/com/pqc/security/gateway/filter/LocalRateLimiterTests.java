package com.pqc.security.gateway.filter;

import org.junit.jupiter.api.Test;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.IntStream;
import static org.assertj.core.api.Assertions.assertThat;

class LocalRateLimiterTests {
    @Test void throttlesAndRefillsWithMonotonicTime() {
        AtomicLong now = new AtomicLong();
        LocalRateLimiter limiter = new LocalRateLimiter(2, 10, 100, now::get);
        assertThat(limiter.acquire("one").allowed()).isTrue();
        assertThat(limiter.acquire("one").allowed()).isTrue();
        assertThat(limiter.acquire("one").retryAfterSeconds()).isEqualTo(5);
        assertThat(limiter.acquire("two").allowed()).isTrue();
        now.addAndGet(5_000_000_000L);
        assertThat(limiter.acquire("one").allowed()).isTrue();
        assertThat(limiter.acquire("one").allowed()).isFalse();
    }

    @Test void boundsClientMemoryAndReclaimsIdleEntries() {
        AtomicLong now = new AtomicLong();
        LocalRateLimiter limiter = new LocalRateLimiter(2, 10, 1, now::get);
        limiter.acquire("one");
        assertThat(limiter.acquire("two").capacityExceeded()).isTrue();
        now.set(301_000_000_000L);
        assertThat(limiter.acquire("two").allowed()).isTrue();
    }

    @Test void concurrentBurstCannotExceedBucketCapacity() {
        LocalRateLimiter limiter = new LocalRateLimiter(10, 60, 100, () -> 0L);
        long allowed = IntStream.range(0, 100).parallel()
                .filter(index -> limiter.acquire("same-peer").allowed()).count();
        assertThat(allowed).isEqualTo(10);
    }
}
