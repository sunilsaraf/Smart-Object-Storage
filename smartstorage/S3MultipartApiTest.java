package com.example.tieredstorage;

import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class S3MultipartApiTest {

    @Value("${local.server.port}") // Get dynamic test port
    private int port;

    @Test
    public void testMultipartUploadWorkflow() {
        RestAssured.port = port;

        // Initiate Multipart Upload (get uploadId)
        String uploadId = given()
                .post("/api/v1/s3/multipart/initiate/test-bucket/test-object")
                .then()
                .statusCode(200)
                .extract().body().asString();

        // Upload Part 1
        given()
            .header("Content-Type", "application/octet-stream")
            .body("This is Part 1".getBytes())
        .when()
            .put("/api/v1/s3/multipart/upload/" + uploadId + "/1")
        .then()
            .statusCode(200);

        // Upload Part 2
        given()
            .header("Content-Type", "application/octet-stream")
            .body("This is Part 2".getBytes())
        .when()
            .put("/api/v1/s3/multipart/upload/" + uploadId + "/2")
        .then()
            .statusCode(200);

        // Complete Upload
        given()
            .post("/api/v1/s3/multipart/complete/" + uploadId)
        .then()
            .statusCode(200);

        // Verify final file content through a GET request (or backend assertion)
        given()
        .when()
            .get("/api/v1/s3/test-bucket/test-object")
        .then()
            .statusCode(200)
            .body(equalTo("This is Part 1This is Part 2")); // Check combined content
    }

    @Test
    public void testAbortMultipartUpload() {
        RestAssured.port = port;

        // Initiate Multipart Upload
        String uploadId = given()
                .post("/api/v1/s3/multipart/initiate/test-bucket/test-object")
                .then()
                .statusCode(200)
                .extract().body().asString();

        // Upload Part 1
        given()
            .header("Content-Type", "application/octet-stream")
            .body("This is Part 1".getBytes())
        .when()
            .put("/api/v1/s3/multipart/upload/" + uploadId + "/1")
        .then()
            .statusCode(200);

        // Abort Upload
        given()
            .delete("/api/v1/s3/multipart/abort/" + uploadId)
        .then()
            .statusCode(200);

        // Verify parts no longer exist (e.g., check file system manually)
    }
}