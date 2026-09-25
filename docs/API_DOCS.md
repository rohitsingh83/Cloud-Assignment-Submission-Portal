# REST API Specification & Endpoint Documentation

The **Cloud-Based Student Assignment Submission & Feedback Portal** exposes a standard RESTful API compliant with OpenAPI 3.1 specifications.

- **Base URL (Local)**: `http://127.0.0.1:8000/api`
- **Base URL (Production)**: `https://cloud-assignment-portal-backend.onrender.com/api`
- **Interactive Swagger UI**: `/docs`
- **Interactive ReDoc**: `/redoc`

---

## 🔐 1. Authentication Endpoints (`/api/auth`)

### 1.1 Register New User
- **Method**: `POST`
- **Endpoint**: `/api/auth/register`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@cloudportal.edu",
    "password": "SecurePassword123!",
    "role": "student"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "user_id": "4a719c8f-5182-4f40-8b17-09d57a9cf518",
    "name": "Jane Doe",
    "email": "jane@cloudportal.edu",
    "role": "student",
    "created_at": "2026-09-25T07:15:00Z"
  }
  ```

---

### 1.2 User Login
- **Method**: `POST`
- **Endpoint**: `/api/auth/login`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "teacher@cloudportal.edu",
    "password": "TeacherPass123!"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "user_id": "9b817c90-062e-4bfa-9cf7-2178a9c2b4c1",
      "name": "Prof. Sarah Johnson",
      "email": "teacher@cloudportal.edu",
      "role": "teacher"
    }
  }
  ```

---

## 📚 2. Assignment Management (`/api/assignments`)

### 2.1 List All Assignments
- **Method**: `GET`
- **Endpoint**: `/api/assignments`
- **Auth Required**: Yes (`Bearer <token>`)
- **Response (`200 OK`)**:
  ```json
  [
    {
      "assignment_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
      "course_id": "c1",
      "course_code": "CS-401",
      "course_name": "Cloud Computing & Distributed Systems",
      "title": "Cloud Capstone: Distributed Object Store Engine",
      "description": "Design an S3-compatible path partitioned object store...",
      "deadline": "2026-10-02T18:00:00Z",
      "max_marks": 100,
      "allowed_file_types": "pdf,docx,zip",
      "max_file_size_mb": 25,
      "has_submitted": true,
      "submission_status": "SUBMITTED",
      "student_marks": null
    }
  ]
  ```

---

### 2.2 Create New Assignment
- **Method**: `POST`
- **Endpoint**: `/api/assignments`
- **Auth Required**: Yes (`role: teacher | admin`)
- **Request Body**:
  ```json
  {
    "course_id": "c1",
    "title": "FastAPI JWT Microservices Architecture",
    "description": "Implement stateless JWT authentication with RBAC guards.",
    "deadline": "2026-10-15T23:59:59Z",
    "max_marks": 100,
    "allowed_file_types": "pdf,zip",
    "max_file_size_mb": 25
  }
  ```
- **Response (`201 Created`)**:
  Returns the created assignment object.

---

### 2.3 Export Grades to CSV
- **Method**: `GET`
- **Endpoint**: `/api/assignments/{assignment_id}/export-csv`
- **Auth Required**: Yes (`role: teacher | admin`)
- **Response (`200 OK`)**:
  - `Content-Type`: `text/csv; charset=utf-8`
  - `Content-Disposition`: `attachment; filename=grades_CS-401.csv`
  - Body:
    ```csv
    Student Name,Email,Submission File,Submitted At (UTC),Status,Marks (Out of 100),Feedback
    Alex Rivera,alex@cloudportal.edu,alex_capstone.pdf,2026-09-24T10:15:00Z,GRADED,94.5,"Outstanding cloud architecture!"
    ```

---

## 📤 3. Submissions & Storage (`/api/submissions`)

### 3.1 Upload / Submit Assignment
- **Method**: `POST`
- **Endpoint**: `/api/assignments/{assignment_id}/submit`
- **Auth Required**: Yes (`role: student`)
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file`: `[Binary File Blob]`
- **Response (`201 Created`)**:
  ```json
  {
    "submission_id": "54b20150-7220-4505-9f65-7fb59f7605f2",
    "assignment_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
    "assignment_title": "Cloud Capstone",
    "file_name": "alex_capstone.pdf",
    "file_size_bytes": 1048576,
    "submitted_at": "2026-09-24T10:15:00Z",
    "submission_status": "SUBMITTED",
    "max_marks": 100
  }
  ```

---

### 3.2 In-Browser Document Preview
- **Method**: `GET`
- **Endpoint**: `/api/submissions/{submission_id}/preview`
- **Auth Required**: Yes (Bearer header or `?token=<jwt_token>`)
- **Response (`200 OK`)**:
  - `Content-Type`: `application/pdf` (or `image/png`, `text/plain`)
  - `Content-Disposition`: `inline; filename="alex_capstone.pdf"`

---

### 3.3 Download File from Cloud Storage
- **Method**: `GET`
- **Endpoint**: `/api/submissions/{submission_id}/download`
- **Auth Required**: Yes (Bearer header or `?token=<jwt_token>`)
- **Response (`200 OK`)**:
  - `Content-Type`: `application/octet-stream`
  - `Content-Disposition`: `attachment; filename="alex_capstone.pdf"`

---

## ⚖️ 4. Plagiarism & Evaluation

### 4.1 Plagiarism / Similarity Check
- **Method**: `GET`
- **Endpoint**: `/api/submissions/{submission_id}/similarity-check`
- **Auth Required**: Yes (`role: teacher | admin`)
- **Response (`200 OK`)**:
  ```json
  {
    "submission_id": "54b20150-7220-4505-9f65-7fb59f7605f2",
    "max_similarity_score": 3.28,
    "risk_level": "LOW RISK (ORIGINAL)",
    "risk_color": "emerald",
    "verdict": "Submission appears original with high unique content index.",
    "total_compared": 4,
    "matches": [
      {
        "peer_submission_id": "e93643e5-...",
        "peer_student_name": "Emily Chen",
        "peer_file_name": "emily_submission.pdf",
        "similarity_score": 3.28
      }
    ]
  }
  ```

---

### 4.2 Grade Submission
- **Method**: `POST`
- **Endpoint**: `/api/submissions/{submission_id}/grade`
- **Auth Required**: Yes (`role: teacher | admin`)
- **Request Body**:
  ```json
  {
    "marks": 94.5,
    "feedback": "Outstanding cloud architecture! Excellent decoupled storage implementation."
  }
  ```
- **Response (`200 OK`)**:
  Returns updated submission object with marks and feedback.
