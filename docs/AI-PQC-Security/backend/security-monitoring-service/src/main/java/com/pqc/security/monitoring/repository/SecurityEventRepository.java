package com.pqc.security.monitoring.repository;

import com.pqc.security.monitoring.entity.SecurityEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SecurityEventRepository extends JpaRepository<SecurityEventEntity, Long> {
    java.util.Optional<SecurityEventEntity> findByEventId(String eventId);

    List<SecurityEventEntity> findTop100ByOrderByOccurredAtDesc();
    List<SecurityEventEntity> findTop100ByUsernameOrderByOccurredAtDesc(String username);
}
