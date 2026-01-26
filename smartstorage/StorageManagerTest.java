@Test
public void testMinIOStorage() throws Exception {
    StorageManager storageManager = new StorageManager(new MinioS3Client());

    File file = new File("test-object.txt");
    Files.write(file.toPath(), "This is a test object.".getBytes());

    // Upload to MinIO
    storageManager.uploadToMinIO("test-object.txt", file);

    // Fetch from MinIO
    File downloadedFile = storageManager.fetchFromMinIO("test-object.txt");
    String content = new String(Files.readAllBytes(downloadedFile.toPath()));
    assertEquals("This is a test object.", content);

    // Delete from MinIO
    storageManager.deleteFromMinIO("test-object.txt");
}