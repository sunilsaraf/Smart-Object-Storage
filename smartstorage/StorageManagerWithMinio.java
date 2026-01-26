@Service
public class StorageManager {

    private final MinioS3Client minioClient;

    @Autowired
    public StorageManager(MinioS3Client minioClient) {
        this.minioClient = minioClient;
    }

    // Save completed objects to MinIO
    public void uploadToMinIO(String objectKey, File file) throws Exception {
        String bucketName = "tiered-storage-bucket";

        // Check if bucket exists, otherwise create it
        try {
            minioClient.createBucket(bucketName);
        } catch (Exception e) {
            System.out.println("Bucket exists: " + bucketName);
        }

        // Upload object to MinIO
        minioClient.uploadToMinIO(bucketName, objectKey, file);
    }

    // Fetch object from MinIO
    public File fetchFromMinIO(String objectKey) throws Exception {
        return minioClient.downloadFromMinIO("tiered-storage-bucket", objectKey);
    }

    // Delete object from MinIO
    public void deleteFromMinIO(String objectKey) {
        minioClient.deleteFromMinIO("tiered-storage-bucket", objectKey);
    }
}