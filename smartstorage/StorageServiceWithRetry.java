package com.example.tieredstorage.services;

import org.springframework.stereotype.Service;

import java.io.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
public class StorageService {

    private final String TEMP_DIR = "./temp-multipart/";
    private final Map<String, MultipartUploadState> uploadStateMap = new ConcurrentHashMap<>();
    private final ExecutorService executor = Executors.newFixedThreadPool(10);

    public StorageService() {
        new File(TEMP_DIR).mkdirs();
    }

    // Retryable upload for parts
    public void uploadPartWithRetry(String uploadId, int partNumber, byte[] partData, int retryLimit) {
        CompletableFuture.runAsync(() -> {
            int retries = 0;
            long backoff = 1000; // Initial backoff: 1 second

            while (retries <= retryLimit) {
                try {
                    System.out.println("Attempting to upload part " + partNumber + " (retry " + retries + ")");
                    // Attempt to upload the part
                    uploadPart(uploadId, partNumber, partData);

                    // If successful, exit retry loop
                    System.out.println("Part " + partNumber + " uploaded successfully.");
                    return;
                } catch (IOException e) {
                    retries++;
                    System.err.println("Failed to upload part " + partNumber + ": " + e.getMessage());

                    // Apply exponential backoff
                    try {
                        Thread.sleep(backoff);
                        backoff *= 2; // Double the backoff time
                    } catch (InterruptedException ie) {
                        // Handle interruption
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Retry process interrupted", ie);
                    }
                }
            }

            // If retries are exhausted
            throw new RuntimeException("Exceeded retry limit for part " + partNumber);
        }, executor);
    }

    public void uploadPart(String uploadId, int partNumber, byte[] partData) throws IOException {
        MultipartUploadState state = getUploadState(uploadId);

        // Save the part to a temporary directory
        File partFile = new File(state.getUploadPath() + "part" + partNumber);
        try (FileOutputStream fos = new FileOutputStream(partFile)) {
            fos.write(partData);
        }

        // Mark the part as completed
        state.getCompletedParts().add(partNumber);
    }

    public MultipartUploadState getUploadProgress(String uploadId) {
        return getUploadState(uploadId);
    }

    public void completeMultipartUpload(String uploadId) throws IOException {
        MultipartUploadState state = getUploadState(uploadId);
        List<File> partFiles = new ArrayList<>();

        for (int partNumber : state.getCompletedParts()) {
            partFiles.add(new File(state.getUploadPath() + "part" + partNumber));
        }

        // Ensure parts are ordered by part number
        partFiles.sort(Comparator.comparing(File::getName));

        // Combine all parts into a single file
        File finalFile = new File(TEMP_DIR + state.getObjectKey());
        try (FileOutputStream fos = new FileOutputStream(finalFile)) {
            for (File part : partFiles) {
                Files.copy(part.toPath(), fos);
            }
        }

        // Clean up
        partFiles.forEach(File::delete);
        uploadStateMap.remove(uploadId);
    }

    private MultipartUploadState getUploadState(String uploadId) {
        if (!uploadStateMap.containsKey(uploadId)) {
            throw new IllegalArgumentException("Invalid uploadId: " + uploadId);
        }
        return uploadStateMap.get(uploadId);
    }
}