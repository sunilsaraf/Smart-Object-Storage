@Test
public void testRetryOnFailedUploads() {
    // Initiate upload
    String uploadId = given()
            .post("/api/v1/s3/multipart/initiate/test-bucket/test-object")
            .then().statusCode(200)
            .extract().asString();

    // Upload Part 1
    given().body("Part 1".getBytes())
            .put("/api/v1/s3/multipart/upload/" + uploadId + "/1")
            .then().statusCode(200);

    // Simulate failure for Part 2: Upload fails intentionally
    given().body("Part 2".getBytes())
            .put("/api/v1/s3/multipart/upload/" + uploadId + "/2")
            .then().statusCode(500); // Simulated failure

    // Check progress (Part 2 will be marked failed)
    given()
            .get("/api/v1/s3/multipart/progress/" + uploadId)
            .then().statusCode(200)
            .body("completedParts.size()", equalTo(1))
            .body("failedParts", hasItem(2));

    // Retry Part 2 upload
    given().body("Part 2".getBytes())
            .post("/api/v1/s3/multipart/retry/" + uploadId + "/2")
            .then().statusCode(200);

    // Verify final completeness
    given().post("/api/v1/s3/multipart/complete/" + uploadId)
            .then().statusCode(200);
}