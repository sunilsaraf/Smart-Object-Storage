package com.example.tieredstorage.services;

import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;
import org.springframework.stereotype.Service;

import java.util.Arrays;

@Service
public class S3LifecycleService {

    private final S3Client s3;

    public S3LifecycleService() {
        this.s3 = S3Client.builder()
                .region(software.amazon.awssdk.regions.Region.US_EAST_1) // Change to your region
                .build();
    }

    // Create a lifecycle policy
    public void createLifecyclePolicy(String bucketName) {
        LifecycleRule hotToWarmRule = LifecycleRule.builder()
                .id("MoveToInfrequentAccess") // Rule Name
                .filter(LifecycleRuleFilter.builder().build()) // Apply to all objects
                .status(ExpirationStatus.ENABLED)
                .transitions(Arrays.asList(
                        Transition.builder()
                                .storageClass(StorageClass.STANDARD_IA) // Move to Warm
                                .days(30) // After 30 days
                                .build(),
                        Transition.builder()
                                .storageClass(StorageClass.GLACIER) // Move to Cold
                                .days(90) // After 90 days
                                .build()
                ))
                .build();

        LifecycleConfiguration lifecycleConfiguration = LifecycleConfiguration.builder()
                .rules(hotToWarmRule)
                .build();

        PutBucketLifecycleConfigurationRequest request =
                PutBucketLifecycleConfigurationRequest.builder()
                        .bucket(bucketName)
                        .lifecycleConfiguration(lifecycleConfiguration)
                        .build();

        s3.putBucketLifecycleConfiguration(request);
        System.out.println("Lifecycle policy created for bucket: " + bucketName);
    }

    // Get the lifecycle policy for a bucket
    public void getLifecyclePolicy(String bucketName) {
        GetBucketLifecycleConfigurationRequest request =
                GetBucketLifecycleConfigurationRequest.builder()
                        .bucket(bucketName)
                        .build();

        GetBucketLifecycleConfigurationResponse response = s3.getBucketLifecycleConfiguration(request);
        System.out.println("Lifecycle rules for bucket: " + bucketName);
        response.rules().forEach(rule -> System.out.println(rule));
    }

    // Delete the lifecycle policy for a bucket
    public void deleteLifecyclePolicy(String bucketName) {
        DeleteBucketLifecycleRequest request =
                DeleteBucketLifecycleRequest.builder()
                        .bucket(bucketName)
                        .build();

        s3.deleteBucketLifecycle(request);
        System.out.println("Lifecycle policy deleted for bucket: " + bucketName);
    }
}