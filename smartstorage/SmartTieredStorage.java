import java.util.*;
import java.util.concurrent.*;

// Storage Tier Enum
enum Tier {
    HOT,
    WARM,
    COLD
}

// Object Metadata Class
class ObjectMetadata {
    String objectId;
    Tier tier;
    long lastAccessed;
    long size; // Size of the object in bytes

    public ObjectMetadata(String objectId, Tier tier, long lastAccessed, long size) {
        this.objectId = objectId;
        this.tier = tier;
        this.lastAccessed = lastAccessed;
        this.size = size;
    }
}

// Object Storage Manager
class TieredStorageManager {
    private final Map<String, ObjectMetadata> metadataStore = new ConcurrentHashMap<>();
    private final ScheduledExecutorService policyEngine = Executors.newSingleThreadScheduledExecutor();
    
    // Simulate Storage Tiers
    private final Map<Tier, List<String>> storageTiers = new EnumMap<>(Tier.class);

    public TieredStorageManager() {
        for (Tier tier : Tier.values()) {
            storageTiers.put(tier, new ArrayList<>());
        }
        // Schedule Policy Engine to Run Periodically
        policyEngine.scheduleAtFixedRate(this::enforcePolicies, 1, 1, TimeUnit.MINUTES);
    }

    // Add Object
    public void addObject(String objectId, long size) {
        ObjectMetadata metadata = new ObjectMetadata(objectId, Tier.HOT, System.currentTimeMillis(), size);
        metadataStore.put(objectId, metadata);
        storageTiers.get(Tier.HOT).add(objectId);
    }

    // Simulate Object Access
    public void accessObject(String objectId) {
        if (metadataStore.containsKey(objectId)) {
            ObjectMetadata metadata = metadataStore.get(objectId);
            metadata.lastAccessed = System.currentTimeMillis();
            System.out.println("Accessed Object: " + objectId + " in Tier: " + metadata.tier);
        } else {
            System.out.println("Object Not Found!");
        }
    }

    // Periodic Policy Evaluation
    private void enforcePolicies() {
        long now = System.currentTimeMillis();
        for (ObjectMetadata metadata : metadataStore.values()) {
            long age = now - metadata.lastAccessed;
            switch (metadata.tier) {
                case HOT:
                    if (age > TimeUnit.HOURS.toMillis(1)) { // Move to WARM
                        moveToTier(metadata, Tier.WARM);
                    }
                    break;
                case WARM:
                    if (age > TimeUnit.DAYS.toMillis(1)) { // Move to COLD
                        moveToTier(metadata, Tier.COLD);
                    }
                    break;
                case COLD:
                    // Cold tier objects stay in cold storage
                    break;
            }
        }
    }

    // Move Object to Another Tier
    private void moveToTier(ObjectMetadata metadata, Tier newTier) {
        storageTiers.get(metadata.tier).remove(metadata.objectId);
        storageTiers.get(newTier).add(metadata.objectId);
        System.out.println("Moving Object: " + metadata.objectId + " from " + metadata.tier + " to " + newTier);
        metadata.tier = newTier;
    }

    // Shutdown Policy Engine
    public void shutdown() {
        policyEngine.shutdown();
    }
}

// Main Class
public class SmartTieredStorage {
    public static void main(String[] args) throws InterruptedException {
        TieredStorageManager manager = new TieredStorageManager();

        // Simulate Adding Objects to Storage
        manager.addObject("Object1", 1024);
        manager.addObject("Object2", 2048);

        // Simulate Access Patterns
        Thread.sleep(5000);
        manager.accessObject("Object1");

        Thread.sleep(5000);
        manager.accessObject("Object2");

        // Keep Running
        Thread.sleep(TimeUnit.MINUTES.toMillis(2));
        manager.shutdown();
    }
}