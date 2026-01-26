package com.example.tieredstorage.storage;

import com.backblaze.erasure.ReedSolomon;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class ColdStorage implements ObjectStorage {

    private final String storagePath = "./storage/cold/";
    private static final int DATA_SHARDS = 6;  // Number of original shards
    private static final int PARITY_SHARDS = 3; // Number of parity shards
    private static final int TOTAL_SHARDS = DATA_SHARDS + PARITY_SHARDS;

    public ColdStorage() {
        new File(storagePath).mkdirs();
    }

    @Override
    public void putObject(String objectId, byte[] data) throws IOException {
        // Divide the data into shards
        int shardSize = (data.length + DATA_SHARDS - 1) / DATA_SHARDS; // Round up
        byte[][] shards = new byte[TOTAL_SHARDS][shardSize];
        for (int i = 0; i < DATA_SHARDS; i++) {
            System.arraycopy(data, i * shardSize, shards[i], 0, Math.min(shardSize, data.length - i * shardSize));
        }

        // Add parity shards
        ReedSolomon reedSolomon = ReedSolomon.create(DATA_SHARDS, PARITY_SHARDS);
        reedSolomon.encodeParity(shards, 0, shardSize);

        // Write shards into separate files
        for (int i = 0; i < TOTAL_SHARDS; i++) {
            try (FileOutputStream fos = new FileOutputStream(storagePath + objectId + ".shard" + i)) {
                fos.write(shards[i]);
            }
        }
    }

    @Override
    public byte[] getObject(String objectId) throws IOException {
        // Load shards from files
        byte[][] shards = new byte[TOTAL_SHARDS][];
        boolean[] shardPresent = new boolean[TOTAL_SHARDS];
        int shardSize = 0;

        for (int i = 0; i < TOTAL_SHARDS; i++) {
            if (Files.exists(Paths.get(storagePath + objectId + ".shard" + i))) {
                shards[i] = Files.readAllBytes(Paths.get(storagePath + objectId + ".shard" + i));
                shardSize = shards[i].length;
                shardPresent[i] = true;
            }
        }

        // Reconstruct data if shards are missing
        ReedSolomon reedSolomon = ReedSolomon.create(DATA_SHARDS, PARITY_SHARDS);
        reedSolomon.decodeMissing(shards, shardPresent, 0, shardSize);

        // Combine the original shards into the full data
        byte[] data = new byte[shardSize * DATA_SHARDS];
        for (int i = 0; i < DATA_SHARDS; i++) {
            System.arraycopy(shards[i], 0, data, i * shardSize, Math.min(data.length - i * shardSize, shardSize));
        }
        return data;
    }

    @Override
    public void deleteObject(String objectId) throws IOException {
        for (int i = 0; i < TOTAL_SHARDS; i++) {
            Files.deleteIfExists(Paths.get(storagePath + objectId + ".shard" + i));
        }
    }

    @Override
    public File exportObject(String objectId) {
        throw new UnsupportedOperationException("Export is not supported for erasure-coded objects.");
    }
}