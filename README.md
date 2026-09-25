<div align="center">
  <h1>☁️ Cloud-Based Student Assignment Submission &amp; Feedback Portal 🎓</h1>
  <p><strong>An Industry-Grade Full-Stack Cloud Application Demonstrating Decoupled Object Storage, Stateless Microservices, Multi-Tenant RBAC, and Plagiarism Analytics</strong></p>

  [![Live Web App](https://img.shields.io/badge/Live%20Web%20App-Online%20%26%20Public-brightgreen?logo=googlechrome&logoColor=white)](https://cloud-assignment-portal-backend.onrender.com)
  [![Backend Status](https://img.shields.io/badge/Backend-Render%20Live-46E3B7?logo=render&logoColor=white)](https://cloud-assignment-portal-backend.onrender.com)
  [![Supabase](https://img.shields.io/badge/Cloud-Supabase%20Ready-3ECF8E?logo=supabase&logoColor=white)](supabase_schema.sql)
  [![FastAPI](https://img.shields.io/badge/API-FastAPI%200.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
  [![Tests](https://img.shields.io/badge/Tests-23%20Passed-success?logo=pytest&logoColor=white)](tests/)
  [![Contributing](https://img.shields.io/badge/Contributions-Welcome-orange.svg)](CONTRIBUTING.md)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
</div>

---

## 🌐 Live Deployments & Cloud Endpoints

| Component | Platform | URL / Endpoint | Health Status |
| :--- | :--- | :--- | :--- |
| **🌐 Live Web Application (Full-Stack UI + API)** | **Render Cloud** | [**cloud-assignment-portal-backend.onrender.com**](https://cloud-assignment-portal-backend.onrender.com) | 🟢 **100% Live & Public** |
| **Backend API Gateway & Docs** | **Swagger UI** | [cloud-assignment-portal-backend.onrender.com/docs](https://cloud-assignment-portal-backend.onrender.com/docs) | 🟢 Interactive Docs |
| **Cloud Health Check** | **Render Probe** | [cloud-assignment-portal-backend.onrender.com/api/health](https://cloud-assignment-portal-backend.onrender.com/api/health) | 🟢 200 OK Healthy |
| **Optional Edge CDN Deployment** | **Vercel** | [Deploy to Vercel Guide](docs/DEPLOYMENT.md#frontend-deployment-on-vercel) | ⚡ 1-Click Import |
| **Local Development** | **Uvicorn / Localhost**| [http://127.0.0.1:8000](http://127.0.0.1:8000) | 🟢 Active |

### 🔑 Pre-Seeded Live Demo Profiles
You can test every role in the portal immediately using the 1-Click login buttons on the homepage or manual credentials:

| Role | Email | Password | Allowed Capabilities |
| :--- | :--- | :--- | :--- |
| **Faculty / Teacher** | `teacher@cloudportal.edu` | `TeacherPass123!` | Create assignments, preview submissions in-browser, run plagiarism checks, enter grades/feedback, export CSV grade rosters. |
| **Student (Alex)** | `student@cloudportal.edu` | `StudentPass123!` | View coursework deadlines, upload submissions (or click "Use Sample PDF"), view server UTC deadline status, inspect faculty feedback. |
| **Student (Emily)** | `emily@cloudportal.edu` | `StudentPass123!` | Track late submission penalties and peer similarity index. |

---

## 📖 Executive Summary

The **Cloud-Based Student Assignment Submission & Feedback Portal** is a production-ready, cloud-native educational application that eliminates paper submissions and ad-hoc email attachments. Architected following modern **12-Factor Cloud Application principles**, the platform provides:

1. **Decoupled Cloud Object Storage**: Binary file payloads (PDFs, ZIPs) are completely decoupled from transactional database tables, avoiding database buffer thrashing and optimizing cloud costs.
2. **Stateless JWT Authentication with RBAC**: Signed HMAC-SHA256 tokens enable seamless horizontal autoscaling across cloud instances with zero sticky-session overhead.
3. **Tamper-Proof UTC Deadline Validation**: All deadline checks are computed using server-side NTP-synchronized UTC clocks, preventing client-side clock tampering.
4. **Built-In Plagiarism & Peer Similarity Scanner**: Automatic n-gram Jaccard set similarity scans detect duplicate submissions and quantify overlap across peer cohorts.
5. **In-Browser Document Preview**: Allows instant evaluation of PDFs, code, and text directly within the grading desk without local file downloads.
6. **Institutional CSV Grade Export**: Generates standardized class grade sheets with submission timestamps and qualitative evaluations.

---

## ☁️ Cloud Architecture & Microservice Topology

```mermaid
flowchart TD
    subgraph ClientLayer ["Client & Edge Delivery Layer (Vercel)"]
        Browser["User Web Browser (Student & Faculty)"]
        VercelEdge["Vercel Global Edge CDN<br/>(SPA Static Delivery & TLS)"]
    end

    subgraph ComputeLayer ["Compute & API Gateway Layer (Render)"]
        RenderService["Render Web Service<br/>(Containerized FastAPI ASGI Application)"]
        AuthGuard["Stateless JWT / RBAC Guard<br/>(PBKDF2-HMAC-SHA256)"]
        DeadlineEngine["Server UTC Deadline Clock<br/>(NTP-Synchronized Enforcement)"]
        PlagiarismEngine["Plagiarism Scanner<br/>(n-gram Jaccard Set Similarity)"]
        PreviewDispatcher["Inline MIME Preview Dispatcher<br/>(PDF / Code Streamer)"]
    end

    subgraph DataLayer ["Decoupled Cloud Data & Storage Layer"]
        RelationalDB[("Cloud Relational Database<br/>SQLite (Local/Demo) &bull; PostgreSQL (Cloud Prod)<br/>(Users, Courses, Assignments, Grades & Audit Logs)")]
        ObjectVault[("Cloud Object Storage Vault<br/>S3 / GCS Path Partitioned<br/>assignments/{aid}/{sid}/{file}")]
    end

    Browser -->|HTTPS / Edge CDN| VercelEdge
    VercelEdge -->|Async REST / JSON| RenderService
    RenderService --> AuthGuard
    RenderService --> DeadlineEngine
    RenderService --> PlagiarismEngine
    RenderService --> PreviewDispatcher
    RenderService -->|ACID SQL Connection Pool| RelationalDB
    RenderService -->|Byte Stream / Partition Keys| ObjectVault
```

---

## 📸 Application Architecture & Interface Visuals

> 💡 **Visual Assets Directory**: Looking for individual high-res diagrams to post on LinkedIn, resumes, or PPT presentations? Visit the dedicated [**`screenshots/` Catalog**](./screenshots/README.md).

<div align="center">
  <h3>🏗️ Multi-Tenant Cloud Architecture Diagram</h3>
  <a href="screenshots/architecture_diagram.svg"><img src="screenshots/architecture_diagram.svg" alt="Cloud Architecture Diagram" width="100%"/></a>
  <br/><br/>
  
  <h3>📊 Faculty Grading Desk & Student Assignment Portal</h3>
  <a href="screenshots/dashboard_preview.svg"><img src="screenshots/dashboard_preview.svg" alt="Dashboard Preview" width="100%"/></a>
  <br/><br/>

  <h3>🔐 Institutional Authentication & 1-Click Demo Profiles</h3>
  <a href="screenshots/login_portal_preview.svg"><img src="screenshots/login_portal_preview.svg" alt="Login Portal Preview" width="85%"/></a>
  <br/><br/>

  <h3>📝 Faculty Rubric Grading, Qualitative Feedback & Presets</h3>
  <a href="screenshots/grading_evaluation_preview.svg"><img src="screenshots/grading_evaluation_preview.svg" alt="Grading Evaluation Preview" width="85%"/></a>
  <br/><br/>
  
  <h3>⚡ End-to-End Assignment Submission & Evaluation Pipeline</h3>
  <a href="screenshots/submission_flow.svg"><img src="screenshots/submission_flow.svg" alt="Submission Flow" width="100%"/></a>
  <br/><br/>
  
  <h3>✨ Built-In Cloud Plagiarism & Peer Similarity Scanner</h3>
  <a href="screenshots/plagiarism_scanner_preview.svg"><img src="screenshots/plagiarism_scanner_preview.svg" alt="Plagiarism Scanner" width="85%"/></a>
  <br/><br/>

  <h3>📄 In-Browser Document Preview with Cloud Asset Streaming</h3>
  <a href="screenshots/file_preview_modal.svg"><img src="screenshots/file_preview_modal.svg" alt="File Preview Modal" width="85%"/></a>
</div>


---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS, FontAwesome 6 | Responsive, zero-bloat Single Page Application |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Starlette | High-performance asynchronous ASGI REST API Gateway |
| **Security & Auth** | `python-jose` (JWT), PBKDF2-HMAC-SHA256 (100k rounds) | Enterprise cryptographic access control & RBAC |
| **Cloud Database** | SQLite (Thread-safe Local) &bull; PostgreSQL (Cloud) | ACID transactional metadata persistence |
| **Cloud Storage** | Decoupled S3-Compatible Storage Driver | Multi-tenant isolated file vault with path traversal protection |
| **Similarity Engine** | n-gram Shingling + Jaccard Set Similarity | Automated plagiarism detection across peer submissions |
| **Containerization** | Docker, Docker Compose | Consistent runtime across local, PaaS, and hyperscale clouds |
| **Edge Hosting** | Vercel (Frontend CDN), Render (Backend Compute) | Multi-cloud decoupled production deployment |
| **Testing** | Pytest (23 Tests) + Programmatic Walkthrough (12 Steps) | Automated continuous quality verification |

---

## ⚡ Supabase Cloud Integration (PostgreSQL + S3 Storage)

EduCloud features **native Supabase support** for production enterprise deployments:
- 🐘 **Supabase Managed PostgreSQL**: Run ACID transactional database queries with connection pooling.
- 🪣 **Supabase Cloud Object Storage**: Store PDFs, DOCX, and ZIP submissions in dedicated `assignments` buckets with global CDN streaming.

### 1-Click Supabase Setup:
1. Create a project at [**supabase.com**](https://supabase.com).
2. Go to the **SQL Editor**, paste the contents of [**`supabase_schema.sql`**](supabase_schema.sql), and click **Run**.
3. Add your Supabase credentials to `.env` or your Render environment variables:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-or-service-role-key
   SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   STORAGE_DRIVER=supabase
   ```
4. Start the app: `python main.py`. The `/api/health` probe will automatically confirm your Supabase connection!

---

## 🧪 Automated Test Suite (23 / 23 Tests Passed)

The repository includes a comprehensive automated test suite covering all functional, security, Supabase cloud drivers, and edge-case requirements:

```bash
# Execute the test suite
pytest -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: Cloud-Assignment-Submission-Portal
collected 23 items

tests/test_portal.py::test_01_student_registration PASSED                [  4%]
tests/test_portal.py::test_02_teacher_login PASSED                       [  8%]
tests/test_portal.py::test_03_invalid_login PASSED                       [ 13%]
tests/test_portal.py::test_04_student_dashboard_authorization PASSED     [ 17%]
tests/test_portal.py::test_05_teacher_dashboard_rbac PASSED              [ 21%]
tests/test_portal.py::test_06_teacher_creates_assignment PASSED          [ 26%]
tests/test_portal.py::test_07_student_views_assignments PASSED           [ 30%]
tests/test_portal.py::test_08_valid_submission_on_time PASSED            [ 34%]
tests/test_portal.py::test_09_invalid_extension_rejected PASSED          [ 39%]
tests/test_portal.py::test_10_late_submission_detected PASSED            [ 43%]
tests/test_portal.py::test_11_resubmission_replaces_old_file PASSED      [ 47%]
tests/test_portal.py::test_12_rbac_student_cross_view_blocked PASSED     [ 52%]
tests/test_portal.py::test_13_teacher_grades_submission PASSED           [ 56%]
tests/test_portal.py::test_14_marks_above_maximum_rejected PASSED        [ 60%]
tests/test_portal.py::test_15_student_views_feedback PASSED              [ 65%]
tests/test_portal.py::test_16_authorized_file_download PASSED            [ 69%]
tests/test_portal.py::test_17_preview_submission_file PASSED             [ 73%]
tests/test_portal.py::test_18_similarity_check_endpoint PASSED           [ 78%]
tests/test_portal.py::test_19_export_grades_csv PASSED                   [ 82%]
tests/test_supabase.py::test_supabase_health_in_api_probe PASSED        [ 86%]
tests/test_supabase.py::test_supabase_service_initialization PASSED      [ 91%]
tests/test_supabase.py::test_supabase_public_url_generation PASSED       [ 95%]
tests/test_supabase.py::test_postgres_cursor_placeholder_adaptation PASSED [100%]

============================= 23 passed in 3.65s ==============================
```

---

## ⚡ Quickstart & Local Execution

### Option 1: 1-Click Launchers (Windows)
```cmd
# Start the live application server
run_dev.bat

# Or run tests
test.bat
```

### Option 2: Command Line (Linux / macOS / Windows)
```bash
# 1. Clone repository
git clone https://github.com/your-username/Cloud-Assignment-Submission-Portal.git
cd Cloud-Assignment-Submission-Portal

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install locked dependencies
pip install -r requirements.txt

# 4. Start the application
python main.py
```
Open **`http://127.0.0.1:8000`** in your browser!

---

## 🚀 Cloud Deployment (Vercel + Render)

### Backend Deployment on Render
1. Push repository to GitHub.
2. In Render, create a new **Web Service** from your repository.
3. Set **Build Command**: `pip install -r requirements.txt`.
4. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Add environment variables: `SECRET_KEY`, `JWT_SECRET`, `ALLOWED_ORIGINS=*`, `MAX_FILE_SIZE_MB=25`.
6. Click **Deploy**. Your API will be live at `https://<service-name>.onrender.com`.

### Frontend Deployment on Vercel
1. In Vercel, click **Add New Project** and import the repository.
2. Set **Root Directory** to `frontend`.
3. Add environment variable: `API_BASE=https://<your-render-app>.onrender.com`.
4. Click **Deploy**. Your frontend is live globally on Vercel Edge CDN!

For full deployment instructions (including Docker and GCP Cloud Run), see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## 📚 Complete Documentation Index

| Document | Purpose |
| :--- | :--- |
| 📄 **[Project Report](docs/PROJECT_REPORT.md)** | Full academic course project report with problem statement, system design, and conclusions. |
| ☁️ **[Cloud Concepts Deep Dive](docs/CLOUD_CONCEPTS.md)** | Technical breakdown of SaaS/PaaS/IaaS, decoupled object storage, stateless auth, and multi-tenancy. |
| 🚀 **[Cloud Deployment Guide](docs/DEPLOYMENT.md)** | Step-by-step instructions for Vercel, Render, Docker Compose, and Google Cloud Run. |
| 💼 **[Interview & Viva Preparation](docs/INTERVIEW_PREP.md)** | 20+ technical placement questions and defense answers. |
| 🔌 **[REST API Documentation](docs/API_DOCS.md)** | Detailed endpoint schemas, request/response models, and status codes. |

---

## ⚖️ Academic License & Disclaimer
*This project was developed strictly for academic, educational, and placement demonstration purposes as part of a Cloud Computing curriculum. All seed student names, emails, and student submissions are purely synthetic.*

---

## 👨‍💻 Author & Attribution
**Rohit Singh**  
*Cloud Computing Course Project — 2026*  
GitHub: [@rohitsingh83](https://github.com/rohitsingh83)
