package com.example.tieredstorage.controllers;

import com.example.tieredstorage.models.ObjectMetadata;
import com.example.tieredstorage.services.MetadataService;
import com.example.tieredstorage.services.StorageService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/s3")
public class StorageController {

    @Autowired
    private StorageService storageService;

    @Autowired
    private MetadataService metadataService;

    // 1. LIST objects in a bucket with optional prefix, maxKeys, and continuationToken
    @GetMapping("/{bucketName}")
    public ResponseEntity<?> listObjects(
            @PathVariable String bucketName,
            @RequestParam(required = false) String prefix,
            @RequestParam(required = false, defaultValue = "10") int maxKeys,
            @RequestParam(required = false) String continuationToken) {

        List<ObjectMetadata> allObjects = metadataService.getObjectsInBucket(bucketName);

        // Optional prefix filtering
        if (prefix != null) {
            allObjects = allObjects.stream()
                    .filter(o -> o.getObjectId().startsWith(prefix))
                    .collect(Collectors.toList());
        }

        // Pagination logic
        int startIndex = continuationToken != null ? Integer.parseInt(continuationToken) : 0;
        int endIndex = Math.min(startIndex + maxKeys, allObjects.size());

        // Response with objects and nextContinuationToken if pagination remains
        List<ObjectMetadata> pagedObjects = allObjects.subList(startIndex, endIndex);
        String nextToken = endIndex < allObjects.size() ? String.valueOf(endIndex) : null;

        return ResponseEntity.ok(
                new S3ListResult(pagedObjects, nextToken)
        );
    }

    // 2. HEAD object metadata
    @HeadMapping("/{bucketName}/{objectKey}")
    public ResponseEntity<?> headObject(
            @PathVariable String bucketName,
            @PathVariable String objectKey) {

        ObjectMetadata metadata = metadataService.getObjectMetadata(objectKey);
        if (metadata == null) {
            return ResponseEntity.notFound().build();
        }

        // Return metadata as part of headers
        return ResponseEntity.ok()
                .header("Content-Length", String.valueOf(metadata.getSize()))
                .header("Tier", metadata.getTier())
                .header("Last-Modified", metadata.getLastAccessed().toString())
                .build();
    }
}

// List API Result Model
class S3ListResult {
    private final List<ObjectMetadata> objects;
    private final String nextContinuationToken;

    public S3ListResult(List<ObjectMetadata> objects, String nextContinuationToken) {
        this.objects = objects;
        this.nextContinuationToken = nextContinuationToken;
    }

    public List<ObjectMetadata> getObjects() {
        return objects;
    }

    public String getNextContinuationToken() {
        return nextContinuationToken;
    }
}