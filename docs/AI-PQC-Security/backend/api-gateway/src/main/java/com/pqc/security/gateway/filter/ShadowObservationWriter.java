package com.pqc.security.gateway.filter;

import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.StringJoiner;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;

/** No request-thread file IO; queue overflow and writer failures only drop telemetry. */
@Component
@ConditionalOnProperty(name = "security.shadow.enabled", havingValue = "true")
public final class ShadowObservationWriter implements AutoCloseable {
    private final ArrayBlockingQueue<String> queue = new ArrayBlockingQueue<>(256);
    private final BufferedWriter writer;
    private final Thread worker;
    private final MeterRegistry meters;
    private volatile boolean accepting = true;
    private volatile boolean failed;

    public ShadowObservationWriter(@Value("${security.shadow.output:}") String filename, MeterRegistry meters) throws IOException {
        if (filename.isBlank()) throw new IllegalArgumentException("Explicit shadow output path is required");
        Path path = Path.of(filename).toAbsolutePath();
        Files.createDirectories(path.getParent());
        writer = Files.newBufferedWriter(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        this.meters = meters;
        worker = new Thread(this::drain, "gateway-shadow-writer");
        worker.setDaemon(true);
        worker.start();
    }
    public void record(ShadowRequestHistory.Snapshot snapshot, int status) {
        record(snapshot, status, UUID.randomUUID().toString());
    }
    public void record(ShadowRequestHistory.Snapshot snapshot, int status, String observationId) {
        StringJoiner features = new StringJoiner(",");
        snapshot.features().forEach((key, value) -> features.add("\"" + key + "\":" + value));
        // IDs and feature keys are server-generated; no user-supplied strings enter the record.
        String schema = snapshot.features().containsKey("context_is_new") ? "gateway-peer-shadow-v2" : "gateway-peer-shadow-v1";
        String line = "{\"schema\":\"" + schema + "\",\"shadow_only\":true,\"observation_id\":\""
                + observationId + "\",\"peer_id\":\"" + snapshot.peerId() + "\",\"features\":{" + features
                + "},\"outcome\":{\"status\":" + status + "}}";
        if (!accepting || failed || !queue.offer(line)) meters.counter("gateway_shadow_dropped_total").increment();
    }
    private void drain() {
        long bytesWritten = 0;
        try (writer) {
            while (accepting || !queue.isEmpty()) {
                String line = queue.poll(100, TimeUnit.MILLISECONDS);
                if (line != null) {
                    // Records are ASCII; include a conservative two-byte newline budget.
                    if (bytesWritten + line.length() + 2 > 10L * 1024 * 1024) {
                        failed = true;
                        accepting = false;
                        queue.clear();
                        meters.counter("gateway_shadow_file_limit_total").increment();
                        break;
                    }
                    writer.write(line);
                    writer.newLine();
                    writer.flush();
                    bytesWritten += line.length() + 2;
                    meters.counter("gateway_shadow_recorded_total").increment();
                }
            }
        } catch (IOException | InterruptedException exception) {
            failed = true;
            meters.counter("gateway_shadow_writer_failures_total").increment();
            if (exception instanceof InterruptedException) Thread.currentThread().interrupt();
        }
    }
    @Override public void close() {
        accepting = false;
        try { worker.join(1500); }
        catch (InterruptedException exception) { Thread.currentThread().interrupt(); }
        if (worker.isAlive()) worker.interrupt();
    }
}
