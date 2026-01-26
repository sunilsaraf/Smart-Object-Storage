package com.example.tieredstorage.services;

import software.amazon.awssdk.auth.credentials.EnvironmentVariableCredentialsProvider;
import software.amazon.awssdk.auth.credentials.ProfileCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Files;

@Service
public class S3ClientService {

    private final S3Client s3;

    public S3ClientService() {
        // Create S3 Client (Use ProfileCredentialsProvider or EnvironmentVariableCredentialsProvider)
        this.s3 = S3Client.builder()
                .region(Region.US_EAST_1) // Update this to your desired AWS region
                .credentialsProvider(EnvironmentVariableCredentialsProvider.create())
                .build();
    }

    // Upload file to S3
    public void uploadToS3(String bucketName, String objectKey, File file) throws Exception {
        PutObjectRequest request = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

        s3.putObject(request, file.toPath());
        System.out.println("File uploaded to S3: " + objectKey);
    }

    // Download file from S3
    public File downloadFromS3(String bucketName, String objectKey) throws Exception {
        File localFile = new File("./cache/" + objectKey);
        if (!localFile.getParentFile().exists()) {
            localFile.getParentFile().mkdirs();
        }

        // Download the specified file from S3 to local cache
        GetObjectRequest request = GetObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

        s3.getObject(request, localFile.toPath());
        System.out.println("File downloaded from S3: " + objectKey);
        return localFile;
    }

    // Delete file from S3
    public void deleteFromS3(String bucketName, String objectKey) {
        DeleteObjectRequest request = DeleteObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

        s3.deleteObject(request);
        System.out.println("File deleted from S3: " + objectKey);
    }
}