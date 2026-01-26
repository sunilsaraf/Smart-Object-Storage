import java.util.concurrent.*;

public class StorageService {

    // Thread pool for processing uploads
    private final ExecutorService executor = Executors.newFixedThreadPool(10); // Allow up to 10 parallel uploads

    public void uploadPartAsync(String uploadId, int partNumber, byte[] partData) {
        executor.submit(() -> {
            try {
                uploadPart(uploadId, partNumber, partData);
                System.out.println("Part " + partNumber + " uploaded successfully.");
            } catch (IOException e) {
                System.err.println("Failed to upload part " + partNumber + ": " + e.getMessage());
            }
        });
    }

    public void shutdownExecutor() {
        executor.shutdown();
    }
}