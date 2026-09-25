# Technical Placement & Viva Interview Preparation Guide

This guide provides targeted technical questions, in-depth architectural explanations, and sample answers for campus placement interviews, technical evaluations, and academic viva defenses.

---

## 📌 Section 1: Cloud Architecture & Design Decisions

### Q1: Why did you choose a decoupled storage architecture instead of storing files inside the database?
**Answer**:
Storing binary files (PDFs, DOCX, ZIP archives) directly as `BLOB` or `BYTEA` in a relational database is a notorious cloud anti-pattern. 
1. **Memory & Cache Thrashing**: Relational databases rely heavily on memory buffer pools (e.g., PostgreSQL `shared_buffers`). Storing multi-megabyte files forces critical table index pages out of RAM, drastically slowing down transactional queries.
2. **Cost Discrepancy**: Provisioned SSD storage attached to database instances (such as AWS EBS io2 or GCP pd-ssd) is up to 10× more expensive per gigabyte than cloud object storage (such as AWS S3 or GCP Cloud Storage).
3. **Backup & Replication Overhead**: Performing database backups (`pg_dump` or point-in-time recovery) becomes painfully slow when tables contain gigabytes of binary payloads.
By separating relational metadata (users, marks, timestamps) into the database and delegating binary payloads to an S3-compatible object store abstraction, both systems operate at maximum efficiency and minimum cost.

---

### Q2: How does the system handle multi-tenancy and prevent students from accessing each other's submissions?
**Answer**:
Multi-tenant security is enforced at three independent layers:
1. **Cryptographic Gateway Authentication**: The user presents a signed JWT token containing their unique `sub` (User ID) and verified `role`.
2. **Route-Level RBAC Guards**: Endpoints enforce role checks (e.g., `require_teacher` blocks any student from listing class-wide submissions or altering grades).
3. **Row-Level Ownership Validation**: When a student requests a file download or details via `/api/submissions/{id}`, the backend executes:
   ```python
   if current_user["role"] == "student" and row["student_id"] != current_user["user_id"]:
       raise HTTPException(status_code=403, detail="Forbidden")
   ```
4. **Storage Path Boundary Resolution**: File paths are partitioned by assignment and student ID (`assignments/{aid}/{sid}/{file}`). Path traversal sequences (such as `../`) are neutralized using canonical path resolution (`.resolve()`) checking `is_relative_to(bucket_dir)`.

---

### Q3: Why is FastAPI preferred over traditional frameworks like Django or Flask for this project?
**Answer**:
1. **High Concurrency & Asynchronous I/O**: FastAPI is built on top of Starlette and ASGI, leveraging Python's `async`/`await` event loop. Streaming file uploads directly to object storage does not block server threads.
2. **Native Request Validation with Pydantic V2**: Request payloads and query params are strictly type-validated at runtime with zero boilerplate, automatically returning descriptive 422 Unprocessable Entity responses for malformed data.
3. **Automated OpenAPI / Swagger Generation**: FastAPI dynamically generates interactive OpenAPI documentation (`/docs`) and ReDoc schemas without third-party plugins.
4. **Lightweight Footprint**: Unlike Django, FastAPI does not impose heavyweight ORM or monolithic templating overhead, making it ideal for containerized microservices on PaaS platforms like Render.

---

## 📌 Section 2: Security & Authentication

### Q4: Explain how password storage is implemented and why standard MD5 or SHA256 is insufficient.
**Answer**:
Simple cryptographic hashes like MD5, SHA1, or unsalted SHA256 are designed for high throughput, making them vulnerable to brute-force and precomputed Rainbow Table attacks (modern GPUs can compute billions of SHA256 hashes per second).

In this project, we implement **NIST SP 800-132 PBKDF2-HMAC-SHA256**:
- **Unique Salt**: A cryptographically secure 16-byte random salt (`os.urandom(16)`) is generated per user, ensuring identical passwords yield distinct hashes.
- **100,000 Iterations**: The key derivation function executes 100,000 rounds of HMAC-SHA256 stretching, making hardware-accelerated attacks computationally infeasible.
- **Constant-Time Comparison**: Verification utilizes `hmac.compare_digest()` to eliminate timing-attack vulnerabilities.

---

### Q5: How do JWTs enable stateless horizontal scaling in cloud deployments?
**Answer**:
With traditional session-based authentication, the server stores session IDs in RAM or shared Redis memory. If the application scales to 5 container replicas behind a load balancer, sticky sessions or centralized session stores are mandatory.

With **JSON Web Tokens (JWT)**:
- All identity claims (`user_id`, `role`, `exp`) are cryptographically signed using HMAC-SHA256 (`HS256`) and sent to the client.
- Every replica node holding the symmetric `SECRET_KEY` can independently verify the token's signature without communicating with a centralized session store or disk.
- If container A receives the login request and container B receives the subsequent file upload, authentication succeeds instantaneously.

---

## 📌 Section 3: Plagiarism & Similarity Scanner

### Q6: How does the built-in Plagiarism and Peer Similarity Scanner work?
**Answer**:
The scanner operates via an automated algorithmic pipeline:
1. **Text Normalization**: Submissions are extracted and converted to lowercased alphanumeric word tokens.
2. **n-gram Shingling ($n=3$)**: The token stream is converted into overlapping 3-word shingles. This captures local syntactic patterns and phrase structures rather than just individual keyword counts.
3. **Jaccard Set Similarity**: The target submission's n-gram set is compared pairwise against all peer submissions within the same assignment:
   $$J(A, B) = \frac{|A \cap B|}{|A \cup B|} \times 100\%$$
4. **Risk Stratification**:
   - `0% – 25%`: **LOW RISK** (Normal academic overlap)
   - `26% – 50%`: **MEDIUM RISK** (Shared starter code / boilerplate)
   - `> 50%`: **HIGH RISK** (Potential unauthorized collaboration / copying)

---

## 📌 Section 4: Edge Cases & Resiliency

### Q7: How does the system handle late submissions and client clock manipulation?
**Answer**:
The client device clock is completely untrusted. All deadline evaluations occur server-side using the server's NTP-synchronized UTC clock:
```python
now_utc = datetime.now(timezone.utc)
deadline_utc = datetime.fromisoformat(assignment["deadline"])
status = "LATE" if now_utc > deadline_utc else "SUBMITTED"
```
Even if a student changes their computer's local time backwards, the cloud server stamps the submission based on UTC, ensuring fairness and integrity.

---

### Q8: What happens if a student resubmits an assignment before it is graded?
**Answer**:
The submission pipeline automatically detects pre-existing submissions:
1. It updates the database record with the new file metadata and new submission timestamp.
2. It resets any previously assigned marks or feedback to `NULL`.
3. It re-evaluates the UTC deadline (if the resubmission occurs after the deadline, its status updates to `LATE`).
4. In object storage, the new file replaces or versions the previous artifact, preventing orphaned file accumulation.

---

### Q9: How is the database layer made resilient across different student operating systems?
**Answer**:
In Python 3.14 on Windows, C-extension packages (such as SQLAlchemy's compiled Cython binaries) can be blocked by Windows Application Control or AppLocker policies without administrative elevation.

To guarantee 100% operational portability, our database layer uses a **pure-Python connection manager over standard-library `sqlite3`**:
- Thread-safe connection context manager with `PRAGMA foreign_keys = ON`.
- Connection timeout handling with automatic rollback on unhandled exceptions.
- Dictionary row factory (`sqlite3.Row`) providing ORM-like attribute access without external binary dependencies.
- Zero-downtime path for PostgreSQL switching simply by providing a `DATABASE_URL`.
