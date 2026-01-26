package com.example.tieredstorage.policies;

import com.example.tieredstorage.models.ObjectMetadata;
import com.example.tieredstorage.services.HybridStorageManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.File;
import java.time.Duration;
import java.time.LocalDateTime;

@Component
public class HybridPolicyEngine {

    @Autowired
    private HybridStorageManager hybridStorageManager;

    // Scheduled task for evaluating and migrating storage tiers
    @Scheduled(fixedRate = 86_400_000) // Run daily
    public void enforcePolicies() {
        System.out.println("Running Hybrid Policy Engine...");

        // This list would typically come from your database
        for (ObjectMetadata metadata : getAllObjectsMetadata()) {
            try {
                LocalDateTime now = LocalDateTime.now();
                Duration inactiveDuration = Duration.between(metadata.getLastAccessed(), now);

                switch (metadata.getTier()) {
                    case "HOT":
                        if (inactiveDuration.toDays() > 10) {
                            moveToWarm(metadata);
                        }
                        break;
                    case "WARM":
                        if (inactiveDuration.toDays() > 30) {
                            moveToCold(metadata);
                        }
                        break;
                }

            } catch (Exception e) {
                System.err.println("Failed to evaluate policy for object: " + metadata.getObjectId());
                e.printStackTrace();
            }
        }
    }

    // Move from MinIO (Hot) → MinIO (Warm)
    private void moveToWarm(ObjectMetadata metadata) throws Exception {
        System.out.println("Moving object to Warm Tier: " + metadata.getObjectId());
        File file = hybridStorageManager.fetchFromHotOrWarm(metadata.getObjectId());
        hybridStorageManager.saveToHotOrWarm(metadata.getObjectId(), file);

        metadata.setTier("WARM"); // Update metadata to Warm
        updateObjectMetadata(metadata);
    }

    // Move from MinIO (Warm) → AWS S3 (Cold)
    private void moveToCold(ObjectMetadata metadata) throws Exception {
        System.out.println("Moving object to Cold Tier: " + metadata.getObjectId());
        File file = hybridStorageManager.fetchFromHotOrWarm(metadata.getObjectId());
        hybridStorageManager.archiveToAWS(metadata.getObjectId(), file);

        hybridStorageManager.deleteFromHotOrWarm(metadata.getObjectId()); // Cleanup MinIO copy
        metadata.setTier("COLD"); // Update metadata to Cold
        updateObjectMetadata(metadata);
    }
}