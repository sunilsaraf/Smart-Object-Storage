package com.example.tieredstorage.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.File;

@Service
public class StorageManager {

    @Autowired
    private S3ClientService s3ClientService;

    private final String BUCKET_NAME = "your-bucket-name";

    // Save completed objects to S3
    public void uploadToCloud(String objectKey, File file) throws Exception {
        s3ClientService.uploadToS3(BUCKET_NAME, objectKey, file);
        System.out.println("Object uploaded to S3: " + objectKey);
    }

    // Download object from S3 for local cache
    public File fetchFromCloud(String objectKey) throws Exception {
        return s3ClientService.downloadFromS3(BUCKET_NAME, objectKey);
    }

    // Delete object from S3
    public void deleteFromCloud(String objectKey) {
        s3ClientService.deleteFromS3(BUCKET_NAME, objectKey);
    }
}