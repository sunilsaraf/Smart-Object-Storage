package com.example.tieredstorage.controllers;

import com.example.tieredstorage.services.StorageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.*;
import java.nio.file.*;

@RestController
@RequestMapping("/api/v1/s3/multipart")
public class MultipartUploadController {

    @Autowired
    private StorageService storageService;

    // 1. Initiate multipart upload
    @PostMapping("/initiate/{bucketName}/{objectKey}")
    public ResponseEntity<?> initiateMultipartUpload(
            @PathVariable String bucketName,
            @PathVariable String objectKey) {

        String uploadId = storageService.initiateMultipartUpload(bucketName, objectKey);
        return ResponseEntity.ok(uploadId); // Send back the unique uploadId
    }

    // 2. Upload part
    @PutMapping("/upload/{uploadId}/{partNumber}")
    public ResponseEntity<?> uploadPart(
            @PathVariable String uploadId,
            @PathVariable int partNumber,
            @RequestBody byte[] partData) throws IOException {

        storageService.uploadPart(uploadId, partNumber, partData);
        return ResponseEntity.ok("Part uploaded successfully.");
    }

    // 3. Complete upload
    @PostMapping("/complete/{uploadId}")
    public ResponseEntity<?> completeMultipartUpload(
            @PathVariable String uploadId) throws IOException {

        storageService.completeMultipartUpload(uploadId);
        return ResponseEntity.ok("Multipart upload completed successfully.");
    }

    // 4. Abort upload
    @DeleteMapping("/abort/{uploadId}")
    public ResponseEntity<?> abortMultipartUpload(
            @PathVariable String uploadId) throws IOException {

        storageService.abortMultipartUpload(uploadId);
        return ResponseEntity.ok("Multipart upload aborted.");
    }
}