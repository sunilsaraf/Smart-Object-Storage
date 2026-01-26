package com.example.tieredstorage;

import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class S3ListApiTest {

    @Value("${local.server.port}") // Get dynamic test port
    private int port;

    @Test
    public void testListObjects() {
        RestAssured.port = port;

        // Test the LIST API
        given()
            .queryParam("prefix", "test")
            .queryParam("maxKeys", 2)
        .when()
            .get("/api/v1/s3/test-bucket")
        .then()
            .statusCode(200)
            .body("objects.size()", lessThanOrEqualTo(2)) // Ensure maxKeys works
            .body("nextContinuationToken", notNullValue()) // Ensure pagination token is returned
            .body("objects[0].objectId", startsWith("test")); // Check filtered prefix
    }
}