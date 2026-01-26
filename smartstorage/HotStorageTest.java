package com.example.tieredstorage.storage;

import org.junit.jupiter.api.Test;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

public class HotStorageTest {

    @Test
    public void testPutAndGetObject() throws IOException {
        HotStorage hotStorage = new HotStorage();
        String objectId = "test-object";
        byte[] data = "This is a test object.".getBytes();

        // Test PUT
        hotStorage.putObject(objectId, data);

        // Test GET
        byte[] retrievedData = hotStorage.getObject(objectId);
        assertArrayEquals(data, retrievedData);

        // Cleanup
        hotStorage.deleteObject(objectId);
    }

    @Test
    public void testDeleteObject() throws IOException {
        HotStorage hotStorage = new HotStorage();
        String objectId = "test-object";
        byte[] data = "This is a test object.".getBytes();

        // Test PUT
        hotStorage.putObject(objectId, data);

        // Test DELETE
        hotStorage.deleteObject(objectId);
        assertThrows(IOException.class, () -> hotStorage.getObject(objectId)); // Object should no longer exist
    }
}