package com.example.tieredstorage.storage;

import java.io.*;
import java.nio.file.*;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

public class ColdStorage implements ObjectStorage {

    private final String storagePath = "./storage/cold/";

    public ColdStorage() {
        new File(storagePath).mkdirs();
    }

    @Override
    public void putObject(String objectId, byte[] data) throws IOException {
        // Save the compressed object
        try (FileOutputStream fos = new FileOutputStream(storagePath + objectId + ".gz");
             GZIPOutputStream gzipOut = new GZIPOutputStream(fos)) {
            gzipOut.write(data);
        }
    }

    @Override
    public byte[] getObject(String objectId) throws IOException {
        // Decompress and retrieve the object
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (FileInputStream fis = new FileInputStream(storagePath + objectId + ".gz");
             GZIPInputStream gzipIn = new GZIPInputStream(fis)) {
            byte[] buffer = new byte[1024];
            int len;
            while ((len = gzipIn.read(buffer)) > 0) {
                out.write(buffer, 0, len);
            }
        }
        return out.toByteArray();
    }

    @Override
    public void deleteObject(String objectId) throws IOException {
        Files.deleteIfExists(Paths.get(storagePath + objectId + ".gz"));
    }

    @Override
    public File exportObject(String objectId) throws IOException {
        return new File(storagePath + objectId + ".gz");
    }
}