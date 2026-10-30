package com.pqc.security.policy.repository;

import com.pqc.security.policy.entity.PolicyDecisionEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PolicyDecisionRepository extends JpaRepository<PolicyDecisionEntity, Long> {
    List<PolicyDecisionEntity> findTop100ByOrderByDecidedAtDesc();
}
