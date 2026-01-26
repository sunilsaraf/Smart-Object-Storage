package com.example.tieredstorage;

import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static io.restassured.RestAssured.given;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class S3HeadApiTest {

    @Value("${local.server.port}") // Get dynamic test port
    private int port;

    @Test
    public void testHeadObject() {
        RestAssured.port = port;

        // Add object metadata to the database before running the test (mock setup)

        given()
        .when()
            .head("/api/v1/s3/test-bucket/test-object")
        .then()
            .statusCode(200)
            .header("Content-Length", notNullValue())
            .header("Tier", equalTo("HOT"))
            .header("Last-Modified", notNullValue());
    }

    @Test
    public void testHeadObjectNotFound() {
        RestAssured.port = port;

        given()
        .when()
            .head("/api/v1/s3/test-bucket/non-existent-object")
        .then()
            .statusCode(404);
    }
}