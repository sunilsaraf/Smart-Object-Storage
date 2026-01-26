package com.example.tieredstorage.services;

import com.example.tieredstorage.models.ObjectMetadata;
import com.example.tieredstorage.storage.*;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Duration;
import java.time.LocalDateTime;

@Service
public class StorageManager {

    private final ObjectStorage hotStorage = new HotStorage();
    private final ObjectStorage warmStorage = new WarmStorage();
    private final ObjectStorage coldStorage = new ColdStorage();

    // Move object between tiers
    public void moveObjectBetweenTiers(ObjectMetadata metadata, ObjectStorage from, ObjectStorage to) throws IOException {
        byte[] data = from.getObject(metadata.getObjectId());
        to.putObject(metadata.getObjectId(), data);
        from.deleteObject(metadata.getObjectId());
        System.out.printf("Moved object [%s] from %s to %s%n", metadata.getObjectId(), from.getClass().getSimpleName(), to.getClass().getSimpleName());
    }

    // Perform tier transitions based on policies
    public void enforceTieringPolicy(ObjectMetadata metadata) throws IOException {
        long timeSinceLastAccess = Duration.between(metadata.getLastAccessed(), LocalDateTime.now()).toMinutes();

        switch (metadata.getTier()) {
            case "HOT":
                if (timeSinceLastAccess > 10) { // Transition to WARM if untouched for 10+ minutes
                    System.out.println("Moving object to Warm tier...");
                    metadata.setTier("WARM");
                    moveObjectBetweenTiers(metadata, hotStorage, warmStorage);
                }
                break;
            case "WARM":
                if (timeSinceLastAccess > 60) { // Transition to COLD if untouched for 60+ minutes
                    System.out.println("Moving object to Cold tier...");
                    metadata.setTier("COLD");
                    moveObjectBetweenTiers(metadata, warmStorage, coldStorage);
                }
                break;
            case "COLD":
                // Cold objects stay in cold tier
                break;
        }
    }
}