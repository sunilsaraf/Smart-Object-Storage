@RestController
@RequestMapping("/api/v1/s3/multipart")
public class MultipartUploadController {

    @Autowired
    private StorageService storageService;

    @PostMapping("/progress/{uploadId}")
    public ResponseEntity<?> getUploadProgress(@PathVariable String uploadId) {
        MultipartUploadState state = storageService.getUploadProgress(uploadId);
        return ResponseEntity.ok(state);
    }

    @PutMapping("/upload/async/{uploadId}/{partNumber}")
    public ResponseEntity<?> uploadPartAsync(
            @PathVariable String uploadId,
            @PathVariable int partNumber,
            @RequestBody byte[] data) {

        storageService.uploadPartAsync(uploadId, partNumber, data);
        return ResponseEntity.ok("Upload in progress.");
    }
}