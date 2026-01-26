package com.example.tieredstorage;

import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static io.restassured.RestAssured.given;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class S3StreamingApiTest {

    @Value("${local.server.port}") // Get dynamic test port
    private int port;

    @Test
    public void testLargeFileDownload() {
        RestAssured.port = port;

        given()
        .when()
            .get("/api/v1/s3/download/test-bucket/large-object")
        .then()
            .statusCode(200)
            .header("Content-Type", "application/octet-stream")
            .header("Content-Disposition", "attachment; filename=large-object");

        // Verify streamed file content if necessary (break down into chunks)
    }
}