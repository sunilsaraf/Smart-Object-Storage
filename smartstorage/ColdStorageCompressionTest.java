package com.example.tieredstorage.storage;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.nio.file.Files;

import static org.junit.jupiter.api.Assertions.*;

public class ColdStorageCompressionTest {

    private ColdStorage coldStorage;
    private final String objectId = "test-object";
    private final byte[] data = "This is some test data to compress".getBytes();

    @BeforeEach
    public void setUp() {
        coldStorage = new ColdStorage();
    }

    @AfterEach
    public void tearDown() throws Exception {
        coldStorage.deleteObject(objectId);
    }

    @Test
    public void testCompressionAndDecompression() throws Exception {
        // Store the object (compression happens here)
        coldStorage.putObject(objectId, data);

        // Retrieve the object (decompression happens here)
        byte[] retrievedData = coldStorage.getObject(objectId);

        // Verify the decompressed data matches the original data
        assertArrayEquals(data, retrievedData, "Decompressed data should match the original data.");

        // Verify compressed file size is smaller than the original
        File compressedFile = new File("./storage/cold/" + objectId + ".gz");
        assertTrue(compressedFile.exists(), "Compressed file should exist in storage.");
        assertTrue(compressedFile.length() <= data.length, "Compressed file size should not exceed original data.");
    }

    @Test
    public void testDeleteCompressedObject() throws Exception {
        // Store the object
        coldStorage.putObject(objectId, data);

        // Delete the object
        coldStorage.deleteObject(objectId);

        // Verify the file no longer exists
        File compressedFile = new File("./storage/cold/" + objectId + ".gz");
        assertFalse(compressedFile.exists(), "Compressed file should be deleted.");
    }
}