@RestController
@RequestMapping("/api/v1/s3/multipart")
public class MultipartUploadController {

    @Autowired
    private StorageService storageService;

    // Query upload progress
    @GetMapping("/progress/{uploadId}")
    public ResponseEntity<?> getUploadProgress(@PathVariable String uploadId) {
        MultipartUploadState state = storageService.getUploadProgress(uploadId);
        return ResponseEntity.ok(state);
    }

    // Retry an upload for a specific part
    @PostMapping("/retry/{uploadId}/{partNumber}")
    public ResponseEntity<?> retryFailedPart(
            @PathVariable String uploadId,
            @PathVariable int partNumber,
            @RequestBody byte[] partData) {

        try {
            storageService.uploadPartWithRetry(uploadId, partNumber, partData, 3);
            return ResponseEntity.ok("Retry for part " + partNumber + " initiated.");
        } catch (RuntimeException e) {
            return ResponseEntity.internalServerError()
                    .body("Failed to retry part " + partNumber + ": " + e.getMessage());
        }
    }
}