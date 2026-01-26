package com.example.tieredstorage.storage;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.nio.file.Files;

import static org.junit.jupiter.api.Assertions.*;

public class ColdStorageErasureCodingTest {

    private ColdStorage coldStorage;
    private final String objectId = "test-object";
    private final byte[] data = "This is some test data for erasure coding".getBytes();

    @BeforeEach
    public void setUp() {
        coldStorage = new ColdStorage();
    }

    @AfterEach
    public void tearDown() throws Exception {
        for (int i = 0; i < 9; i++) { // DATA_SHARDS + PARITY_SHARDS = 6 + 3
            Files.deleteIfExists(new File("./storage/cold/" + objectId + ".shard" + i).toPath());
        }
    }

    @Test
    public void testErasureCodingStorageAndRetrieval() throws Exception {
        // Store the object (sharding and encoding happens here)
        coldStorage.putObject(objectId, data);

        // Validate all shards are present
        for (int i = 0; i < 9; i++) { // TOTAL_SHARDS = DATA_SHARDS + PARITY_SHARDS
            File shard = new File("./storage/cold/" + objectId + ".shard" + i);
            assertTrue(shard.exists(), "Shard " + i + " should exist in cold storage.");
        }

        // Retrieve the object (decoding happens here)
        byte[] retrievedData = coldStorage.getObject(objectId);
        assertArrayEquals(data, retrievedData, "Reconstructed data should match the original data.");
    }

    @Test
    public void testReconstructionWithMissingShards() throws Exception {
        // Store the object
        coldStorage.putObject(objectId, data);

        // Simulate the loss of two shards
        Files.deleteIfExists(new File("./storage/cold/" + objectId + ".shard0").toPath());
        Files.deleteIfExists(new File("./storage/cold/" + objectId + ".shard1").toPath());

        // Retrieve the object (should reconstruct despite missing shards)
        byte[] retrievedData = coldStorage.getObject(objectId);
        assertArrayEquals(data, retrievedData, "Reconstructed data should match original despite missing shards.");
    }

    @Test
    public void testReconstructionFailsWithTooManyMissingShards() throws Exception {
        // Store the object
        coldStorage.putObject(objectId, data);

        // Simulate the loss of five shards (DATA_SHARDS = 6, losing 5 means data can't be reconstructed)
        for (int i = 0; i < 5; i++) {
            Files.deleteIfExists(new File("./storage/cold/" + objectId + ".shard" + i).toPath());
        }

        // Attempt retrieval (should fail)
        assertThrows(RuntimeException.class, () -> coldStorage.getObject(objectId),
                "Should throw an exception when reconstruction is not possible due to excessive shard loss.");
    }
}