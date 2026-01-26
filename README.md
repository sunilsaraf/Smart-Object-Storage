# **Smart Tiered Hybrid Object Storage**

## **Overview**
The **Smart Tiered Hybrid Object Storage** system is designed to manage object storage across multiple tiers based on access frequency, balancing performance and cost. The system integrates **AWS S3** for cloud-based archive storage and **MinIO** for on-premise active storage, ensuring seamless scalability, cost-efficiency, and performance.

### Use Case
- Tiered storage management for **Hot**, **Warm**, and **Cold** tiers.
- Minimize operational costs by automatically migrating inactive data to lower-cost storage.
- Hybrid setup for leveraging **local on-prem storage** (e.g., MinIO) for fast operations and **AWS S3** for archival storage.

---

## **System Highlights**

### **Architecture**
This architecture has three key components:
1. **Hot Tier**:
   - Data is actively accessed and stored in **MinIO** using fast on-prem resources (e.g., NVMe/SSD).
   - Ideal for high-performance operations.

2. **Warm Tier**:
   - For less-accessed data stored in **MinIO's warm storage** (e.g., HDD).
   - Intermediate stage before migration to the cloud.

3. **Cold Tier**:
   - Archived data moved to **AWS S3 Glacier** or **S3 Infrequent Access**.
   - Lowest-cost tier for long-term archival storage.

### Architecture Diagram

```plaintext
+-------------------+                     +-------------------+                     +----------------+
|                   |                     |                   |                     |                |
|    MinIO          |                     |    MinIO          |                     |    AWS S3      |
|                   |                     |                   |                     |                |
| Hot Tier (Active) |----Policy Engine--->| Warm Tier (Idle)  |----Policy Engine--->| Archive (Cloud)|
|                   |                     |                   |                     |                |
+-------------------+                     +-------------------+                     +----------------+
                    |---------------- Monitor Tiers and Migrate -------------------|
```

---

### **Key Features**

1. **Hybrid Storage Design**:
   - Combines on-premise (MinIO) and cloud-based (S3) solutions.
   - Utilizes MinIO for active access and AWS S3 for long-term archival storage.

2. **Smart Policy Management**:
   - Policies decide tier transitions based on object access frequency and age.
   - Automatically migrates old or idle objects to appropriate tiers.

3. **Automatic Tier Management**:
   - **Hot Tier**: Frequently accessed data.
   - **Warm Tier**: Intermediate-tier for infrequently accessed data.
   - **Cold Tier**: Archival tier on S3 using Glacier or Standard_IA storage classes.

4. **Fault-Tolerant Multipart Uploads**:
   - Retries failed uploads with exponential backoff.
   - Tracks incomplete uploads for resumption.

5. **S3 API Compatibility**:
   - Provides S3-compatible interfaces for all object storage operations.

6. **Administrator Control**:
   - Allows admins to query object states, override tiering policies, and manage hybrid storage.

---

## **Why This Project Is Unique**

### Key Differentiators:
1. **Hybrid Design**:
   - Combines **on-premise storage** with **cloud storage** effortlessly.
   - Balances between performance, control, and cost-efficiency.

2. **Automated Smart Policies**:
   - Intelligent tiering policies simplify storage management.
   - No manual migration — objects are automatically relocated across tiers based on usage.

3. **Cost-Efficiency**:
   - Reduces storage costs by archiving unused data in AWS S3’s cost-efficient storage classes.
   - Utilizes MinIO for reducing cloud egress charges and latency costs for active workloads.

4. **Future-Proof**:
   - Designed to integrate with other S3-compatible platforms beyond AWS (e.g., Wasabi, Ceph).

---

## **Installation Guide**

### **1. Install MinIO**
#### For Local Setup:
```bash
wget https://dl.min.io/server/minio
chmod +x minio
./minio server /data --console-address ":9001"
```

#### For Docker Setup:
```bash
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=password123" \
  minio/minio server /data --console-address ":9001"
```

**Default Credentials:**
- Username: `admin`
- Password: `password123`

---

### **2. Setup AWS S3**
1. Ensure you have an **AWS account** with an S3 bucket created.
2. Use IAM **Access Key** and **Secret Key** for API access.

---

### **3. Environment Configuration**
Update environment variables for the system:
```bash
export MINIO_ACCESS_KEY="admin"
export MINIO_SECRET_KEY="password123"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_REGION="us-east-1"
```

---

## **Run the Application**

1. Clone the project:
   ```bash
   git clone https://github.com/your-repository-url/tiered-storage.git
   cd tiered-storage
   ```

2. Build the project:
   ```bash
   ./gradlew build
   ```

3. Start the application:
   ```bash
   java -jar build/libs/tiered-storage-0.0.1-SNAPSHOT.jar
   ```

4. Open the API in your browser:
   - Swagger Docs: `http://localhost:8080/swagger-ui.html`

---

## **Sample API Usage**

### **1. Upload Object**
```curl
curl -X PUT "http://localhost:8080/api/v1/s3/minio-tiered-storage/sample-object" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @sample-data.txt
```

### **2. Migrate Object to AWS S3**
```curl
curl -X POST "http://localhost:8080/api/v1/s3/move-to-cold?objectId=sample-object"
```

### **3. Fetch Object**
- From MinIO (Hot/Warm):
```curl
curl -X GET "http://localhost:8080/api/v1/s3/fetch/hot?objectId=sample-object"
```

- From AWS S3:
```curl
curl -X GET "http://localhost:8080/api/v1/s3/fetch/cold?objectId=sample-object"
```

---

## **Admin Operations**
1. **Check Object Metadata**:
   - Query metadata for all objects, their storage tiers, and their age.

2. **Policy Management**:
   - Override default tiering policies and manage object migrations manually.

---

## **How Tiering Works**

The policy engine migrates data automatically:
- **Hot → Warm**: If inactive for **10 days**.
- **Warm → Cold (S3)**: If inactive for **30 days**.

---

## **Top Use Cases**
1. **Cost-Optimized Archival**:
   - Move long-term archival data to cost-effective AWS S3 Glacier.
2. **Data Backup and Recovery**:
   - Maintain active objects locally while archiving older versions securely in the cloud.
3. **Hybrid Cloud Storage**:
   - Use MinIO for on-prem data and AWS S3 as a secondary, fail-safe tier in the cloud.

---

## **Future Enhancements**
1. **Add Reporting and Monitoring**:
   - Use Prometheus and Grafana to visualize tier usage and costs.
2. **Distributed Setup**:
   - Deploy in a distributed setup using Kubernetes for high availability.
3. **Support Other S3-Compatible Systems**:
   - Extend to platforms like Ceph, Wasabi, or DigitalOcean Spaces.

---

## **Contributing**
1. Fork the repository.
2. Submit a pull request with detailed descriptions.
3. Review issues and suggest improvements.

Let's build better together!

---

## **License**
Licensed under the MIT License. See LICENSE for more details.