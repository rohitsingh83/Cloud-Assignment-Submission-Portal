import io
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import init_db
from backend.cloud.database_service import seed_initial_demo_data

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    seed_initial_demo_data()
    yield

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_token(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]

# 1. Student Registration Test
def test_01_student_registration(client):
    unique_email = f"student_{datetime.now().timestamp()}@cloudportal.edu"
    res = client.post("/api/auth/register", json={
        "name": "New Student",
        "email": unique_email,
        "password": "Password123!",
        "role": "student"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == unique_email
    assert data["role"] == "student"

# 2. Teacher Login Test
def test_02_teacher_login(client):
    res = client.post("/api/auth/login", json={
        "email": "teacher@cloudportal.edu",
        "password": "TeacherPass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "teacher"

# 3. Invalid Login Test
def test_03_invalid_login(client):
    res = client.post("/api/auth/login", json={
        "email": "teacher@cloudportal.edu",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

# 4. Student Dashboard Authorization
def test_04_student_dashboard_authorization(client):
    token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    res = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_assignments" in data

# 5. Teacher Dashboard Authorization & Forbidden for Student
def test_05_teacher_dashboard_rbac(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    res = client.get("/api/dashboard/teacher", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 403

    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    res2 = client.get("/api/dashboard/teacher", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res2.status_code == 200
    assert "total_submissions" in res2.json()

# 6. Teacher Creates Assignment
def test_06_teacher_creates_assignment(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    res = client.post("/api/assignments", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "course_id": "course-uuid-001",
        "title": "Assignment 3: Cloud Microservices",
        "description": "Build and containerize an asynchronous worker queue.",
        "deadline": deadline,
        "max_marks": 100,
        "allowed_file_types": "pdf,docx,zip",
        "max_file_size_mb": 25
    })
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Assignment 3: Cloud Microservices"
    assert data["max_marks"] == 100

# 7. Student Views Assignment List
def test_07_student_views_assignments(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    res = client.get("/api/assignments", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    assignments = res.json()
    assert len(assignments) >= 2
    assert "has_submitted" in assignments[0]

# 8. Valid PDF File Upload (On-time Submission)
def test_08_valid_submission_on_time(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    dummy_file = io.BytesIO(b"%PDF-1.4 Mock Assignment Submission Content")

    res = client.post(
        "/api/assignments/assign-uuid-001/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("my_submission.pdf", dummy_file, "application/pdf")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["submission_status"] == "SUBMITTED"
    assert data["file_name"] == "my_submission.pdf"
    assert "assignments/assign-uuid-001/" in data["storage_path"]

# 9. Invalid File Extension Rejected
def test_09_invalid_extension_rejected(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    malicious_script = io.BytesIO(b"echo 'malicious script'")

    res = client.post(
        "/api/assignments/assign-uuid-001/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("exploit.exe", malicious_script, "application/x-msdownload")}
    )
    assert res.status_code == 400
    assert "Invalid file type" in res.json()["detail"]

# 10. Late Submission Detection
def test_10_late_submission_detected(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    dummy_file = io.BytesIO(b"%PDF-1.4 Late Submission File")

    res = client.post(
        "/api/assignments/assign-uuid-002/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("late_lab.pdf", dummy_file, "application/pdf")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["submission_status"] == "LATE"

# 11. Student Resubmission Workflow
def test_11_resubmission_replaces_old_file(client):
    student_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    revised_file = io.BytesIO(b"%PDF-1.4 Revised Submission Content v2")

    res = client.post(
        "/api/assignments/assign-uuid-001/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("my_submission_v2.pdf", revised_file, "application/pdf")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["file_name"] == "my_submission_v2.pdf"

# 12. Student Cannot View Another Student's Submission
def test_12_rbac_student_cross_view_blocked(client):
    emily_token = get_auth_token(client, "emily@cloudportal.edu", "StudentPass123!")
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")

    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    assert len(alex_subs) > 0
    alex_sub_id = alex_subs[0]["submission_id"]

    res = client.get(f"/api/submissions/{alex_sub_id}", headers={"Authorization": f"Bearer {emily_token}"})
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]

# 13. Teacher Grades Submission with Marks & Written Feedback
def test_13_teacher_grades_submission(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    alex_sub_id = alex_subs[0]["submission_id"]

    res = client.post(
        f"/api/submissions/{alex_sub_id}/grade",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "marks": 94.5,
            "feedback": "Outstanding cloud architecture design! Very clear object storage isolation."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["marks"] == 94.5
    assert data["submission_status"] == "GRADED"
    assert "Outstanding cloud architecture" in data["feedback"]

# 14. Marks Above Maximum Rejected
def test_14_marks_above_maximum_rejected(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    alex_sub_id = alex_subs[0]["submission_id"]

    res = client.post(
        f"/api/submissions/{alex_sub_id}/grade",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "marks": 150.0,
            "feedback": "Impossible score"
        }
    )
    assert res.status_code == 400
    assert "cannot exceed maximum" in res.json()["detail"]

# 15. Student Views Grade and Feedback
def test_15_student_views_feedback(client):
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    alex_sub_id = alex_subs[0]["submission_id"]

    res = client.get(f"/api/submissions/{alex_sub_id}/feedback", headers={"Authorization": f"Bearer {alex_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["marks"] == 94.5
    assert "Outstanding cloud architecture" in data["feedback"]

# 16. Student Download File
def test_16_authorized_file_download(client):
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    alex_sub_id = alex_subs[0]["submission_id"]

    res = client.get(f"/api/submissions/{alex_sub_id}/download", headers={"Authorization": f"Bearer {alex_token}"})
    assert res.status_code == 200
    assert b"%PDF-1.4" in res.content

# 17. In-Browser File Preview
def test_17_preview_submission_file(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    sub_id = alex_subs[0]["submission_id"]

    # Preview with token query param
    res = client.get(f"/api/submissions/{sub_id}/preview?token={teacher_token}")
    assert res.status_code == 200
    assert "inline" in res.headers.get("content-disposition", "")
    assert b"%PDF-1.4" in res.content

# 18. Plagiarism & Similarity Detection
def test_18_similarity_check_endpoint(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    alex_token = get_auth_token(client, "student@cloudportal.edu", "StudentPass123!")
    alex_subs = client.get("/api/submissions/me", headers={"Authorization": f"Bearer {alex_token}"}).json()
    sub_id = alex_subs[0]["submission_id"]

    res = client.get(f"/api/submissions/{sub_id}/similarity-check", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "max_similarity_score" in data
    assert "verdict" in data
    assert "matches" in data

# 19. Export Grades CSV
def test_19_export_grades_csv(client):
    teacher_token = get_auth_token(client, "teacher@cloudportal.edu", "TeacherPass123!")
    assignments = client.get("/api/assignments", headers={"Authorization": f"Bearer {teacher_token}"}).json()
    assign_id = assignments[0]["assignment_id"]

    res = client.get(f"/api/assignments/{assign_id}/export-csv", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert b"Student Name,Email" in res.content
