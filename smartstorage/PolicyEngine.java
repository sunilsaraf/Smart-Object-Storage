package com.example.tieredstorage.policies;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.example.tieredstorage.models.ObjectMetadata;
import com.example.tieredstorage.services.MetadataService;
import com.example.tieredstorage.services.StorageManager;

import java.io.IOException;
import java.util.List;

@Component
public class PolicyEngine {

    private static final Logger logger = LoggerFactory.getLogger(PolicyEngine.class);

    @Autowired
    private MetadataService metadataService;

    @Autowired
    private StorageManager storageManager;

    @Scheduled(fixedRate = 60000)
    public void enforcePolicies() {
        logger.info("Running policy engine...");
        List<ObjectMetadata> allObjects = metadataService.getAllMetadata();

        for (ObjectMetadata metadata : allObjects) {
            try {
                storageManager.enforceTieringPolicy(metadata);
                logger.info("Enforced tiering policy for object {}", metadata.getObjectId());
            } catch (IOException e) {
                logger.error("Error processing object {}: {}", metadata.getObjectId(), e.getMessage());
            }
        }
    }
}