import os
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

from backend.config import BASE_DIR, LOCAL_STORAGE_DIR
from backend.database import init_db, get_db_cursor
from backend.auth import get_password_hash

def generate_minimal_pdf(title: str, author: str, content: str) -> bytes:
    """Generates a valid, minimal PDF 1.4 binary file with custom content."""
    pdf_text = f"""%PDF-1.4
1 0 obj
<< /Title ({title}) /Author ({author}) >>
endobj
2 0 obj
<< /Type /Catalog /Pages 3 0 R >>
endobj
3 0 obj
<< /Type /Pages /Kids [4 0 R] /Count 1 >>
endobj
4 0 obj
<< /Type /Page /Parent 3 0 R /MediaBox [0 0 612 792] /Contents 5 0 R
   /Resources << /Font << /F1 6 0 R >> >> >>
endobj
5 0 obj
<< /Length {len(content) + 100} >>
stream
BT
/F1 16 Tf
50 720 Td
({title}) Tj
/F1 12 Tf
50 680 Td
(Author: {author}) Tj
50 640 Td
({content[:80]}) Tj
ET
endstream
endobj
6 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000078 00000 n
0000000131 00000 n
0000000194 00000 n
0000000324 00000 n
0000000490 00000 n
trailer
<< /Size 7 /Root 2 0 R >>
startxref
570
%%EOF"""
    return pdf_text.encode("latin-1")

def seed_complete_ecosystem():
    print("=" * 70)
    print("  SEEDING COMPLETE CLOUD COMPUTING PORTAL DATASET")
    print("=" * 70)

    init_db()
    storage_root = Path(LOCAL_STORAGE_DIR)
    storage_root.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    with get_db_cursor() as cursor:
        # 1. Teachers
        teachers = [
            ("teacher-uuid-001", "Prof. Sarah Johnson", "teacher@cloudportal.edu", "TeacherPass123!", "teacher"),
            ("teacher-uuid-002", "Dr. Alan Vance", "alan.vance@cloudportal.edu", "TeacherPass123!", "teacher"),
            ("teacher-uuid-003", "Dr. Maya Patel", "maya.patel@cloudportal.edu", "TeacherPass123!", "teacher"),
        ]
        for tid, name, email, pwd, role in teachers:
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (user_id, name, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (tid, name, email, get_password_hash(pwd), role, now_iso))
                print(f"  [+] Teacher Created: {name} ({email})")

        # 2. Students
        students = [
            ("student-uuid-001", "Alex Rivera", "student@cloudportal.edu", "StudentPass123!", "student"),
            ("student-uuid-002", "Emily Chen", "emily@cloudportal.edu", "StudentPass123!", "student"),
            ("student-uuid-003", "Michael Zhang", "michael.zhang@cloudportal.edu", "StudentPass123!", "student"),
            ("student-uuid-004", "Sophia Al-Mansoor", "sophia@cloudportal.edu", "StudentPass123!", "student"),
            ("student-uuid-005", "David Miller", "david.miller@cloudportal.edu", "StudentPass123!", "student"),
        ]
        for sid, name, email, pwd, role in students:
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (user_id, name, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sid, name, email, get_password_hash(pwd), role, now_iso))
                print(f"  [+] Student Created: {name} ({email})")

        # 3. Courses
        courses = [
            ("course-uuid-001", "Cloud Computing & Distributed Systems", "CS-401", "teacher-uuid-001"),
            ("course-uuid-002", "Container Orchestration & Microservices", "CS-402", "teacher-uuid-002"),
            ("course-uuid-003", "Serverless Computing & Cloud Native Apps", "CS-403", "teacher-uuid-003"),
        ]
        for cid, cname, ccode, tid in courses:
            cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", (ccode,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO courses (course_id, course_name, course_code, teacher_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (cid, cname, ccode, tid, now_iso))
                print(f"  [+] Course Created: {ccode} - {cname}")

        # 4. Assignments
        assignments = [
            (
                "assign-uuid-001", "course-uuid-001",
                "Assignment 1: Distributed Object Storage Architecture",
                "Design and document a scalable object storage solution comparing AWS S3, Google Cloud Storage, and Azure Blob.",
                (now + timedelta(days=7)).isoformat(),
                100, "pdf,docx,zip", 25, "teacher-uuid-001"
            ),
            (
                "assign-uuid-002", "course-uuid-001",
                "Assignment 2: Docker Containerization Lab",
                "Containerize a multi-tier web application, configure bridge networks, and inspect resource constraints.",
                (now - timedelta(days=2)).isoformat(), # Past deadline
                50, "pdf,zip", 20, "teacher-uuid-001"
            ),
            (
                "assign-uuid-003", "course-uuid-002",
                "Assignment 3: Kubernetes Ingress & Load Balancing",
                "Configure an NGINX Ingress Controller on a local Minikube/Kind cluster with path-based routing.",
                (now + timedelta(days=12)).isoformat(),
                100, "pdf,docx", 25, "teacher-uuid-002"
            ),
            (
                "assign-uuid-004", "course-uuid-003",
                "Assignment 4: Event-Driven Serverless Pipeline",
                "Implement an image-resizing pipeline triggered automatically on cloud object storage PUT events.",
                (now + timedelta(days=4)).isoformat(),
                75, "pdf,zip", 30, "teacher-uuid-003"
            )
        ]
        for aid, cid, title, desc, deadline, marks, types, max_mb, created_by in assignments:
            cursor.execute("SELECT assignment_id FROM assignments WHERE assignment_id = ?", (aid,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO assignments (
                        assignment_id, course_id, title, description, deadline,
                        max_marks, allowed_file_types, max_file_size_mb, created_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (aid, cid, title, desc, deadline, marks, types, max_mb, created_by, now_iso))
                print(f"  [+] Assignment Created: {title}")

        # 5. Submissions and Physical Files
        sample_submissions = [
            # Graded on-time submission
            (
                "sub-seed-001", "assign-uuid-001", "student-uuid-001",
                "alex_rivera_cloud_storage.pdf", 96.5,
                "Outstanding comparative analysis of S3 vs Azure Blob! Clear diagrams and rigorous latency benchmarks.",
                (now - timedelta(days=3)).isoformat(), "GRADED",
                (now - timedelta(days=1)).isoformat(), "teacher-uuid-001"
            ),
            # Graded on-time submission
            (
                "sub-seed-002", "assign-uuid-001", "student-uuid-002",
                "emily_chen_storage_architecture.pdf", 89.0,
                "Well-structured explanation of eventual consistency. Please elaborate further on multi-region replication costs.",
                (now - timedelta(days=2)).isoformat(), "GRADED",
                (now - timedelta(days=1)).isoformat(), "teacher-uuid-001"
            ),
            # Graded late submission
            (
                "sub-seed-003", "assign-uuid-002", "student-uuid-001",
                "alex_rivera_docker_lab.pdf", 44.0,
                "Docker Compose setup works well. Deducted 5% for late submission penalty according to course policy.",
                (now - timedelta(days=1)).isoformat(), "GRADED", # submitted 1 day ago, deadline was 2 days ago
                (now - timedelta(hours=6)).isoformat(), "teacher-uuid-001"
            ),
            # Pending review (On-time)
            (
                "sub-seed-004", "assign-uuid-001", "student-uuid-003",
                "michael_zhang_distributed_storage.pdf", None,
                None,
                (now - timedelta(hours=14)).isoformat(), "SUBMITTED",
                None, None
            ),
            # Pending review (Late)
            (
                "sub-seed-005", "assign-uuid-002", "student-uuid-002",
                "emily_chen_docker_submission.pdf", None,
                None,
                (now - timedelta(hours=8)).isoformat(), "LATE",
                None, None
            ),
        ]

        for sub_id, aid, sid, fname, marks, feedback, sub_at, status, graded_at, graded_by in sample_submissions:
            cursor.execute("SELECT submission_id FROM submissions WHERE submission_id = ?", (sub_id,))
            if not cursor.fetchone():
                storage_path = f"assignments/{aid}/{sid}/{int(time.time())}_{fname}"
                file_url = f"/api/submissions/download-by-path?path={storage_path}"

                # Create physical PDF in object storage bucket
                physical_path = storage_root / storage_path
                physical_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_bytes = generate_minimal_pdf(
                    title=f"Submission for {aid}",
                    author=f"Student {sid}",
                    content=f"Demonstrating cloud storage decoupled persistence and metadata indexing."
                )
                with open(physical_path, "wb") as f:
                    f.write(pdf_bytes)

                cursor.execute("""
                    INSERT INTO submissions (
                        submission_id, assignment_id, student_id, file_name, file_url,
                        storage_path, file_size_bytes, submitted_at, submission_status,
                        marks, feedback, graded_at, graded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sub_id, aid, sid, fname, file_url,
                    storage_path, len(pdf_bytes), sub_at, status,
                    marks, feedback, graded_at, graded_by
                ))
                print(f"  [+] Submission Seeded: {fname} -> Status: {status} (File: {storage_path})")

    print("=" * 70)
    print("  SEEDING COMPLETE! Full realistic dataset populated successfully.")
    print("=" * 70)

if __name__ == "__main__":
    seed_complete_ecosystem()
