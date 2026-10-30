package com.pqc.security.gateway.filter;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.LongSupplier;

/** Bounded token buckets for a single gateway instance, using monotonic time. */
public final class LocalRateLimiter {
    public record Decision(boolean allowed, long retryAfterSeconds, boolean capacityExceeded) { }
    private static final class Bucket {
        double tokens;
        long updated;
        Bucket(double tokens, long updated) { this.tokens = tokens; this.updated = updated; }
    }
    private final int capacity;
    private final int maxClients;
    private final double tokensPerNanosecond;
    private final long idleExpiryNanos;
    private final LongSupplier ticker;
    private final Map<String, Bucket> buckets = new LinkedHashMap<>();

    public LocalRateLimiter(int capacity, long periodSeconds, int maxClients, LongSupplier ticker) {
        if (capacity < 1 || periodSeconds < 1 || periodSeconds > 86400 || maxClients < 1) {
            throw new IllegalArgumentException("Invalid rate-limit configuration");
        }
        this.capacity = capacity;
        this.maxClients = maxClients;
        this.tokensPerNanosecond = capacity / (periodSeconds * 1_000_000_000.0);
        this.idleExpiryNanos = Math.max(300, periodSeconds * 2) * 1_000_000_000L;
        this.ticker = ticker;
    }

    public synchronized Decision acquire(String client) {
        long now = ticker.getAsLong();
        Bucket bucket = buckets.get(client);
        if (bucket == null) {
            if (buckets.size() >= maxClients) {
                buckets.entrySet().removeIf(entry -> now - entry.getValue().updated >= idleExpiryNanos);
            }
            if (buckets.size() >= maxClients) {
                return new Decision(false, 1, true);
            }
            bucket = new Bucket(capacity, now);
            buckets.put(client, bucket);
        }
        bucket.tokens = Math.min(capacity, bucket.tokens + Math.max(0, now - bucket.updated) * tokensPerNanosecond);
        bucket.updated = now;
        if (bucket.tokens >= 1) {
            bucket.tokens -= 1;
            return new Decision(true, 0, false);
        }
        long retry = Math.max(1, (long) Math.ceil((1 - bucket.tokens) / tokensPerNanosecond / 1_000_000_000.0));
        return new Decision(false, retry, false);
    }
}
