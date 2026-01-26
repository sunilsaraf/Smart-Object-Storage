package com.example.tieredstorage.services;

import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.*;
import java.util.*;

@Service
public class StorageService {

    private final String TEMP_DIR = "./temp-multipart/";

    // Keep track of ongoing uploads
    private final Map<String, List<File>> multipartUploads = new HashMap<>();

    public StorageService() {
        new File(TEMP_DIR).mkdirs();
    }

    // Initiate upload
    public String initiateMultipartUpload(String bucketName, String objectKey) {
        String uploadId = UUID.randomUUID().toString();
        multipartUploads.put(uploadId, new ArrayList<>());
        return uploadId;
    }

    // Upload part
    public void uploadPart(String uploadId, int partNumber, byte[] partData) throws IOException {
        File partFile = new File(TEMP_DIR + uploadId + ".part" + partNumber);
        try (FileOutputStream fos = new FileOutputStream(partFile)) {
            fos.write(partData);
        }
        multipartUploads.get(uploadId).add(partFile);
    }

    // Complete upload
    public void completeMultipartUpload(String uploadId) throws IOException {
        List<File> partFiles = multipartUploads.get(uploadId);
        partFiles.sort(Comparator.comparing(File::getName)); // Ensure parts are in order

        File finalFile = new File(TEMP_DIR + uploadId + "-final");
        try (FileOutputStream fos = new FileOutputStream(finalFile)) {
            for (File part : partFiles) {
                Files.copy(part.toPath(), fos);
                part.delete(); // Clean up part file
            }
        }
        multipartUploads.remove(uploadId);
        System.out.println("Multipart upload finalized at: " + finalFile.getPath());
    }

    // Abort upload
    public void abortMultipartUpload(String uploadId) throws IOException {
        List<File> partFiles = multipartUploads.remove(uploadId);
        if (partFiles != null) {
            for (File part : partFiles) {
                part.delete(); // Cleanup
            }
        }
    }
}