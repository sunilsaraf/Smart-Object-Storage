// State class for tracking multipart upload progress
class MultipartUploadState {
    private final String uploadId;
    private final String bucketName;
    private final String objectKey;
    private final String uploadPath;
    private final Set<Integer> completedParts;
    private final Set<Integer> failedParts; // Track failed parts for resumption

    public MultipartUploadState(String uploadId, String bucketName, String objectKey, String uploadPath) {
        this.uploadId = uploadId;
        this.bucketName = bucketName;
        this.objectKey = objectKey;
        this.uploadPath = uploadPath;
        this.completedParts = ConcurrentHashMap.newKeySet();
        this.failedParts = ConcurrentHashMap.newKeySet();
    }

    public String getUploadId() {
        return uploadId;
    }

    public String getBucketName() {
        return bucketName;
    }

    public String getObjectKey() {
        return objectKey;
    }

    public String getUploadPath() {
        return uploadPath;
    }

    public Set<Integer> getCompletedParts() {
        return completedParts;
    }

    public Set<Integer> getFailedParts() {
        return failedParts;
    }
}