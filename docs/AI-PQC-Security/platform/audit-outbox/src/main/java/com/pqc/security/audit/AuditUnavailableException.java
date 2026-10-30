package com.pqc.security.audit;

public class AuditUnavailableException extends RuntimeException {
    public AuditUnavailableException(Throwable cause) { super("Durable audit storage unavailable", cause); }
}
