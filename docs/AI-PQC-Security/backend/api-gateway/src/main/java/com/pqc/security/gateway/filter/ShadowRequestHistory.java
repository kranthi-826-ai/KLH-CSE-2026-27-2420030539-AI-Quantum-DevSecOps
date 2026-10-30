package com.pqc.security.gateway.filter;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Bounded peer history; only already completed requests enter a snapshot. */
public final class ShadowRequestHistory {
    public record Snapshot(String peerId, Map<String, Double> features, String contextKey) { }
    private record Event(long start, long completed, String route, int status, String contextKey) { }
    private static final class Peer {
        final String id = UUID.randomUUID().toString();
        final List<Event> events = new ArrayList<>();
        long lastActivity;
        Long lastCompletedStart;
    }
    private final Map<String, Peer> peers = new LinkedHashMap<>();
    private final int maxPeers;
    private final int maxEvents;
    private final byte[] contextSecret = new byte[32];
    private static final long FIVE_SECONDS = 5_000_000_000L;
    public ShadowRequestHistory(int maxPeers, int maxEvents) {
        if (maxPeers < 1 || maxPeers > 4096 || maxEvents < 1 || maxEvents > 512)
            throw new IllegalArgumentException("Invalid shadow history bounds");
        this.maxPeers = maxPeers;
        this.maxEvents = maxEvents;
        new java.security.SecureRandom().nextBytes(contextSecret);
    }
    public synchronized Snapshot before(String address, long now, String route, boolean bearer) {
        return snapshot(address, now, route, bearer, "", false);
    }
    public synchronized Snapshot beforeRich(String address, long now, String route, String authorization) {
        boolean bearer = authorization != null && authorization.startsWith("Bearer ") && authorization.length() > 7;
        String key = route + ":no-bearer";
        if (bearer) {
            try {
                var mac = javax.crypto.Mac.getInstance("HmacSHA256");
                mac.init(new javax.crypto.spec.SecretKeySpec(contextSecret, "HmacSHA256"));
                key = route + ":" + java.util.HexFormat.of().formatHex(mac.doFinal(authorization.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            } catch (java.security.GeneralSecurityException exception) { throw new IllegalStateException(exception); }
        }
        return snapshot(address, now, route, bearer, key, true);
    }
    private Snapshot snapshot(String address, long now, String route, boolean bearer, String contextKey, boolean rich) {
        Peer peer = peers.get(address);
        if (peer == null) {
            peers.values().removeIf(p -> now - p.lastActivity > 60_000_000_000L);
            if (peers.size() >= maxPeers) return null; // Skip observation, never reject traffic.
            peer = new Peer();
            peers.put(address, peer);
        }
        peer.lastActivity = now;
        peer.events.removeIf(e -> now - e.completed > FIVE_SECONDS);
        var features = new LinkedHashMap<String, Double>();
        features.put("is_login", route.equals("/api/v1/auth/login") ? 1. : 0.);
        features.put("is_identity_read", route.equals("/api/v1/auth/me") ? 1. : 0.);
        features.put("has_bearer", bearer ? 1. : 0.);
        features.put("has_history", peer.lastCompletedStart == null ? 0. : 1.);
        var prior = peer.events.stream().filter(e -> e.completed < now).toList();
        features.put("prior_requests_1s", (double) prior.stream().filter(e -> now - e.start <= 1_000_000_000L).count());
        features.put("prior_requests_5s", (double) prior.size());
        features.put("prior_401_5s", (double) prior.stream().filter(e -> e.status == 401).count());
        features.put("prior_failed_login_5s", (double) prior.stream().filter(e -> e.status == 401 && e.route.equals("/api/v1/auth/login")).count());
        features.put("seconds_since_previous_start", peer.lastCompletedStart == null ? 5. :
                Math.min(5., Math.max(0., (now - peer.lastCompletedStart) / 1_000_000_000.)));
        if (rich) {
            var context = prior.stream().filter(e -> e.contextKey.equals(contextKey)).toList();
            var sameRoute = prior.stream().filter(e -> e.route.equals(route)).toList();
            features.put("context_prior_requests_5s", (double) context.size());
            features.put("context_prior_401_5s", (double) context.stream().filter(e -> e.status == 401).count());
            features.put("context_prior_success_5s", (double) context.stream().filter(e -> e.status >= 200 && e.status < 300).count());
            features.put("route_prior_requests_5s", (double) sameRoute.size());
            features.put("route_prior_401_5s", (double) sameRoute.stream().filter(e -> e.status == 401).count());
            features.put("route_prior_success_5s", (double) sameRoute.stream().filter(e -> e.status >= 200 && e.status < 300).count());
            features.put("peer_consecutive_401", consecutiveFailures(prior));
            features.put("context_consecutive_401", consecutiveFailures(context));
            features.put("context_is_new", context.isEmpty() ? 1. : 0.);
            features.put("context_last_was_401", lastWasFailure(context));
            features.put("route_last_was_401", lastWasFailure(sameRoute));
            features.put("peer_last_was_401", lastWasFailure(prior));
            features.put("unique_bearer_contexts_5s", (double) prior.stream().filter(e -> !e.contextKey.endsWith(":no-bearer")).map(Event::contextKey).distinct().count());
            features.put("prior_success_5s", (double) prior.stream().filter(e -> e.status >= 200 && e.status < 300).count());
            Long previous = context.stream().map(Event::start).max(Long::compare).orElse(null);
            features.put("seconds_since_context_start", previous == null ? 5. : Math.min(5., Math.max(0., (now-previous)/1_000_000_000.)));
        }
        return new Snapshot(peer.id, Map.copyOf(features), contextKey);
    }
    public synchronized void after(String address, long start, long completed, String route, int status) {
        after(address, start, completed, route, status, "");
    }
    public synchronized void after(String address, long start, long completed, String route, int status, String contextKey) {
        Peer peer = peers.get(address);
        if (peer == null) return;
        peer.events.removeIf(e -> completed - e.completed > FIVE_SECONDS);
        peer.events.add(new Event(start, completed, route, status, contextKey));
        if (peer.events.size() > maxEvents) {
            Event oldest = peer.events.stream().min(java.util.Comparator.comparingLong(Event::completed)).orElseThrow();
            peer.events.remove(oldest);
        }
        peer.lastCompletedStart = peer.lastCompletedStart == null ? start : Math.max(start, peer.lastCompletedStart);
        peer.lastActivity = Math.max(peer.lastActivity, completed);
    }
    private static double consecutiveFailures(List<Event> events) {
        var ordered = events.stream().sorted(java.util.Comparator.comparingLong(Event::completed).reversed()).toList();
        int count = 0;
        for (Event event : ordered) { if (event.status != 401) break; count++; }
        return count;
    }
    private static double lastWasFailure(List<Event> events) {
        return events.stream().max(java.util.Comparator.comparingLong(Event::completed)).map(e -> e.status == 401 ? 1. : 0.).orElse(0.);
    }
}
