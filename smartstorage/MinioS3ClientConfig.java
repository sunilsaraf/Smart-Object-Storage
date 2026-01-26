package com.example.tieredstorage.services;

import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;

public class MinioS3Client {

    private final S3Client s3;

    public MinioS3Client() {
        // Use MinIO credentials and endpoint
        AwsBasicCredentials credentials = AwsBasicCredentials.create(
                "admin", // MinIO Access Key
                "password123" // MinIO Secret Key
        );

        this.s3 = S3Client.builder()
                .endpointOverride(URI.create("http://127.0.0.1:9000")) // MinIO URL
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .region(Region.US_EAST_1) // Region is arbitrary for MinIO
                .build();
    }

    // Upload object to MinIO
    public void uploadToMinIO(String bucketName, String key, File file) {
        s3.putObject(
                PutObjectRequest.builder()
                        .bucket(bucketName)
                        .key(key)
                        .build(),
                file.toPath()
        );
        System.out.println("File uploaded to MinIO: " + key);
    }

    // Download object from MinIO
    public File downloadFromMinIO(String bucketName, String key) throws Exception {
        File localFile = new File("./cache/" + key);

        // Ensure cache directory exists
        new File("./cache").mkdirs();

        s3.getObject(
                GetObjectRequest.builder()
                        .bucket(bucketName)
                        .key(key)
                        .build(),
                localFile.toPath()
        );
        System.out.println("File downloaded from MinIO: " + key);
        return localFile;
    }

    // Delete object from MinIO
    public void deleteFromMinIO(String bucketName, String key) {
        s3.deleteObject(
                DeleteObjectRequest.builder()
                        .bucket(bucketName)
                        .key(key)
                        .build()
        );
        System.out.println("File deleted from MinIO: " + key);
    }
}