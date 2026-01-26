package com.example.tieredstorage.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.File;

@Service
public class HybridStorageManager {

    private final MinioS3Client minioClient; // For local on-prem storage
    private final AWSS3Client awsS3Client;  // For cloud storage on AWS S3

    @Autowired
    public HybridStorageManager(MinioS3Client minioClient, AWSS3Client awsS3Client) {
        this.minioClient = minioClient;
        this.awsS3Client = awsS3Client;
    }

    // Store data locally in MinIO (Hot / Warm Tiers)
    public void saveToHotOrWarm(String objectKey, File file) throws Exception {
        String bucketName = "minio-tiered-storage"; // Bucket for MinIO
        minioClient.ensureBucketExists(bucketName);
        minioClient.uploadToMinIO(bucketName, objectKey, file);
        System.out.println("Saved object in MINIO (Hot/Warm): " + objectKey);
    }

    // Upload data to AWS S3 (Cold / Archive Tier)
    public void archiveToAWS(String objectKey, File file) throws Exception {
        String bucketName = "aws-tiered-storage"; // Bucket for AWS S3
        awsS3Client.ensureBucketExists(bucketName);
        awsS3Client.uploadToS3(bucketName, objectKey, file);
        System.out.println("Archived object to AWS S3 (Cold/Archive): " + objectKey);
    }

    // Fetch objects from MinIO
    public File fetchFromHotOrWarm(String objectKey) throws Exception {
        return minioClient.downloadFromMinIO("minio-tiered-storage", objectKey);
    }

    // Fetch objects from AWS S3
    public File fetchFromCold(String objectKey) throws Exception {
        return awsS3Client.downloadFromS3("aws-tiered-storage", objectKey);
    }

    // Delete objects from MinIO
    public void deleteFromHotOrWarm(String objectKey) {
        minioClient.deleteFromMinIO("minio-tiered-storage", objectKey);
    }

    // Delete objects from AWS S3
    public void deleteFromCold(String objectKey) {
        awsS3Client.deleteFromS3("aws-tiered-storage", objectKey);
    }
}