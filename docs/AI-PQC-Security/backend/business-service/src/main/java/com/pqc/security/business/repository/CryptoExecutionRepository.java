package com.pqc.security.business.repository;

import com.pqc.security.business.entity.CryptoExecutionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CryptoExecutionRepository extends JpaRepository<CryptoExecutionEntity, String> {
    List<CryptoExecutionEntity> findTop100ByOrderByExecutedAtDesc();
    List<CryptoExecutionEntity> findTop100ByUsernameOrderByExecutedAtDesc(String username);
}
