package com.example.tieredstorage.services;

import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class StorageService {

    private final String TEMP_DIR = "./temp-multipart/";

    // State tracking for in-progress multipart uploads
    private final Map<String, MultipartUploadState> uploadStateMap = new ConcurrentHashMap<>();

    public StorageService() {
        new File(TEMP_DIR).mkdirs();
    }

    // Initiate upload and return a unique uploadId
    public String initiateMultipartUpload(String bucketName, String objectKey) {
        String uploadId = UUID.randomUUID().toString();
        String uploadPath = TEMP_DIR + uploadId + "/";
        new File(uploadPath).mkdirs();

        uploadStateMap.put(uploadId, new MultipartUploadState(uploadId, bucketName, objectKey, uploadPath));
        return uploadId;
    }

    // Upload a part and track its completion
    public void uploadPart(String uploadId, int partNumber, byte[] partData) throws IOException {
        MultipartUploadState state = getUploadState(uploadId);

        // Save the part to the temporary directory
        File partFile = new File(state.getUploadPath() + "part" + partNumber);
        try (FileOutputStream fos = new FileOutputStream(partFile)) {
            fos.write(partData);
        }

        // Mark the part as completed
        state.getCompletedParts().add(partNumber);
    }

    // Query upload progress
    public MultipartUploadState getUploadProgress(String uploadId) {
        return getUploadState(uploadId);
    }

    // Complete the multipart upload by combining all parts
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

    // Abort upload and cleanup
    public void abortMultipartUpload(String uploadId) {
        MultipartUploadState state = getUploadState(uploadId);

        // Delete all parts
        File uploadDir = new File(state.getUploadPath());
        for (File file : Objects.requireNonNull(uploadDir.listFiles())) {
            file.delete();
        }
        uploadDir.delete();

        // Remove from state map
        uploadStateMap.remove(uploadId);
    }

    // Retrieve upload state from the map
    private MultipartUploadState getUploadState(String uploadId) {
        if (!uploadStateMap.containsKey(uploadId)) {
            throw new IllegalArgumentException("Invalid uploadId: " + uploadId);
        }
        return uploadStateMap.get(uploadId);
    }
}

// State class for tracking multipart upload progress
class MultipartUploadState {
    private final String uploadId;
    private final String bucketName;
    private final String objectKey;
    private final String uploadPath;
    private final Set<Integer> completedParts;

    public MultipartUploadState(String uploadId, String bucketName, String objectKey, String uploadPath) {
        this.uploadId = uploadId;
        this.bucketName = bucketName;
        this.objectKey = objectKey;
        this.uploadPath = uploadPath;
        this.completedParts = new HashSet<>();
    }

    public String getUploadId() {
        return uploadId;
    }

    public String getBucketName() {
        return bucketName;
    }

    public String getObjectKey() {
        return objectKey;
    }

    public String getUploadPath() {
        return uploadPath;
    }

    public Set<Integer> getCompletedParts() {
        return completedParts;
    }
}