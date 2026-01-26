package com.example.tieredstorage.storage;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class WarmStorage implements ObjectStorage {

    private final String storagePath = "./storage/warm/";

    public WarmStorage() {
        new File(storagePath).mkdirs();
    }

    @Override
    public void putObject(String objectId, byte[] data) throws IOException {
        try (FileOutputStream out = new FileOutputStream(storagePath + objectId)) {
            out.write(data);
        }
    }

    @Override
    public byte[] getObject(String objectId) throws IOException {
        return Files.readAllBytes(Paths.get(storagePath + objectId));
    }

    @Override
    public void deleteObject(String objectId) throws IOException {
        Files.deleteIfExists(Paths.get(storagePath + objectId));
    }

    @Override
    public File exportObject(String objectId) throws IOException {
        return new File(storagePath + objectId);
    }
}