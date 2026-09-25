# ACADEMIC PROJECT REPORT

## PROJECT TITLE:
# Cloud-Based Student Assignment Submission & Feedback Portal

---

### **Abstract**
In modern higher education and corporate training paradigms, physical paper-based coursework submission and unstructured digital submissions via email or chat apps create severe administrative friction, version ambiguity, security risks, and evaluation bottlenecks. This project presents the design and implementation of the **Cloud-Based Student Assignment Submission & Feedback Portal**, an industry-grade, cloud-native educational application. 

The system architecturally separates structured relational application state (users, course definitions, deadlines, evaluation rubrics, submission logs, and qualitative feedback) from unstructured binary payload data (PDF, DOCX, ZIP files). Structured state is managed in an ACID-compliant cloud relational database, while binary attachments are delegated to a scalable cloud object storage system. The portal implements stateless RESTful APIs built on FastAPI, cryptographically secured JWT authentication with Role-Based Access Control (RBAC), and server-side synchronized UTC deadline verification. Empirical testing across functional, security, and edge-case test suites demonstrates robust performance, strict tenant isolation, and zero unauthorized data leakage.

---

### **1. Introduction**
Cloud computing has fundamentally altered software development by providing on-demand, elastic, and utility-metered compute, storage, and networking resources. In academic institutions, Learning Management Systems (LMS) such as Canvas, Blackboard, and Google Classroom serve as the primary bridge between instructional faculty and student cohorts. 

A central challenge in architecting such systems is handling variable file upload volumes while maintaining strict security, auditable deadline enforcement, and low storage costs. This project demonstrates foundational and advanced cloud computing principles by constructing an end-to-end coursework submission and evaluation platform.

---

### **2. Problem Statement**
Manual and legacy digital submission mechanisms present several critical flaws:
1. **Attachment Loss & Inbox Clutter**: Email submissions frequently trigger mailbox quotas, bounce large attachments, or get flagged as spam.
2. **Untrusted Client Clocks**: Submissions validated using client-side device times allow students to artificially manipulate local system clocks to bypass strict submission windows.
3. **Database Performance Degradation**: Storing binary file objects (BLOBs) inside relational database tables bloats the database buffer pool, slows down indexes, complicates backups, and increases database hosting expenses.
4. **Access Control Vulnerabilities**: Insecure file naming and lack of role-based route guards expose student coursework to unauthorized downloads or unauthorized grade modifications.

---

### **3. Objectives**
1. Develop a responsive, cloud-hosted web portal accessible anywhere via modern web standards.
2. Architect a decoupled storage model using a cloud database for metadata and cloud object storage for binary assets.
3. Enforce Role-Based Access Control (RBAC) ensuring strict role separation between Students, Teachers, and Administrators.
4. Implement tamper-proof, server-side UTC deadline tracking that automatically tags submissions as `SUBMITTED` or `LATE`.
5. Provide a closed-loop evaluation workflow where teachers review documents, award numerical marks, and enter qualitative feedback visible directly on the student dashboard.
6. Deliver a 100% free-tier compatible architecture capable of seamless migration to hyperscale cloud providers (AWS, Azure, Google Cloud).

---

### **4. Existing System vs. Proposed System**

| Attribute | Existing / Legacy System | Proposed Cloud-Based Portal |
|:---|:---|:---|
| **Submission Medium** | Physical printouts / Email attachments | Centralized Cloud Web Portal |
| **Storage Architecture** | Local server disks / Database BLOBs | Decoupled Object Storage + Metadata DB |
| **Deadline Validation** | Subjective / Manual / Client timestamps | Server-side UTC NTP-synchronized clocks |
| **Access Control** | Open file links or basic password forms | Cryptographic JWT + Strict RBAC |
| **Grading Workflow** | Manual gradebooks / spreadsheets | Integrated feedback modal & live dashboard |
| **Scalability** | Monolithic server constrained by disk space | Horizontally scalable stateless compute + S3 |

---

### **5. User Roles and Permissions**
- **Student**:
  - Authenticate securely via email and password.
  - Inspect enrolled courses and active coursework deadlines.
  - Upload assignment files with extension and byte-size validation.
  - Resubmit revised assignments before grading.
  - Download only their own submitted documents.
  - Review instructor marks and written commentary.
- **Teacher (Faculty)**:
  - Create, modify, and delete assignments with deadline policies.
  - Inspect student submissions across assigned courses.
  - Download and review submitted files.
  - Award marks validated against maximum points.
  - Provide written constructive feedback.
  - Track real-time submission statistics and pending reviews.
- **Admin**:
  - Superuser access for managing system-wide courses and users.

---

### **6. Cloud Computing Concepts Used**
1. **Software as a Service (SaaS)**: Delivers an end-user educational product accessible on-demand over the internet without client installation.
2. **Platform as a Service (PaaS)**: Built to run seamlessly on managed application platforms (Render, Railway, AWS App Runner).
3. **Infrastructure as a Service (IaaS)**: Architecture mirrors virtualized compute instances (EC2), virtual networks, and block/object volumes.
4. **Cloud Database**: Normalized relational database storing structured entities with foreign key constraints and transactional integrity.
5. **Cloud Object Storage**: Flat namespace key-value object repository with hierarchical path conventions (`assignments/{aid}/{sid}/{file}`).
6. **Stateless RESTful APIs**: Decoupled HTTP endpoints adhering to Richardson Maturity Model Level 2, facilitating horizontal scaling.
7. **Role-Based Access Control (RBAC)**: Security enforcement validating permissions at the endpoint level before dispatching business logic.
8. **Secrets Management & 12-Factor App**: Externalized configuration via environment variables (`.env`).
9. **Cloud Health Probes**: `/api/health` liveness endpoint for cloud load balancers and container orchestrators.

---

### **7. System Architecture & Request Lifecycle**

```
[Student / Teacher Client Browser]
             │ (HTTPS / TLS 1.3)
             ▼
[Reverse Proxy / Cloud CDN / Load Balancer]
             │
             ▼
[FastAPI Application Server (:8000)]
   │
   ├── [JWT Auth & RBAC Dependency Guard]
   │
   ├── [Assignment / Grading Service] ──────► [Cloud Database (SQLite / Postgres)]
   │                                                    ▲
   └── [Submission & Deadline Engine]                   │
             │                                (Metadata & Status)
             ▼
   [Cloud Object Storage (Bucket)]
```

---

### **8. Database & Cloud Storage Schema**
The database schema consists of four core relational entities:
- `users`: User identity, hashed credentials, and role assignments.
- `courses`: Academic courses and assigned faculty instructors.
- `assignments`: Coursework requirements, deadline timestamps, max marks, and file constraints.
- `submissions`: Object storage keys, upload timestamps, deadline status, marks, and feedback strings.

**Why Object Storage Over Database BLOBs?**
- **Buffer Pool Pollution**: Reading large BLOBs evicts frequently queried index pages from database RAM.
- **Backup Speed**: Transaction logs and database dumps become massive when containing binary assets.
- **Cost**: Object storage costs approximately \$0.023/GB/month compared to \$0.115+/GB/month for high-performance provisioned database storage.
- **Direct Streaming**: Object storage supports chunked streaming, resumable uploads, and Content Delivery Network (CDN) caching.

---

### **9. Verification & Test Results**
An automated test suite comprising 16 test cases was executed against the application:
- Student Registration & Login Authentication: **PASS**
- Teacher Authentication & Privilege Verification: **PASS**
- Invalid Credentials Rejection: **PASS**
- Cross-Role Route Protection (Student blocked from Teacher Dashboard): **PASS**
- Assignment Creation & Course Association: **PASS**
- Valid PDF Upload to Object Storage: **PASS**
- Unauthorized File Type Filtering (.exe blocked): **PASS**
- Server-Side UTC Deadline Comparison (On-Time vs Late): **PASS**
- Resubmission Workflow & Object Cleanup: **PASS**
- Cross-Tenant Data Isolation (Student A cannot view Student B): **PASS**
- Faculty Grading & Marks Over-Limit Protection: **PASS**
- Authorized File Download Streaming: **PASS**

---

### **10. Conclusion & Future Scope**
The **Cloud-Based Student Assignment Submission & Feedback Portal** successfully fulfills all design, pedagogical, and cloud architectural requirements. It delivers a resilient, secure, and production-ready solution that bridges software engineering best practices with cloud storage and database paradigms.

**Future Enhancements**:
- Integration with AI/ML microservices for automated plagiarism detection using Sentence-BERT embeddings.
- Serverless event-driven notifications (AWS SNS / Firebase Cloud Messaging) for upcoming deadline alerts.
- Antivirus and malware scanning using containerized ClamAV upon object upload.
