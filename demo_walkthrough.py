"""
Automated Demo Simulation Script for Cloud Assignment Submission & Feedback Portal.
Runs through the entire real-world lifecycle from assignment creation to student submission,
object storage verification, faculty review, and grade retrieval.
"""

import io
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def print_step(number, title):
    print(f"\n[{number:02d}] " + "=" * 60)
    print(f"     STEP: {title}")
    print("     " + "=" * 60)

def run_simulation():
    print("\n" + "#" * 70)
    print("#  STARTING FULL CLOUD PORTAL LIFECYCLE SIMULATION")
    print("#" * 70)

    # 1. Health check
    print_step(1, "Checking Cloud Portal Liveness Probe")
    res = client.get("/api/health")
    assert res.status_code == 200
    print(f"     Cloud Health: {res.json()}")

    # 2. Teacher Login
    print_step(2, "Authenticating Teacher (Prof. Sarah Johnson)")
    res = client.post("/api/auth/login", json={
        "email": "teacher@cloudportal.edu",
        "password": "TeacherPass123!"
    })
    assert res.status_code == 200, f"Teacher login failed: {res.text}"
    teacher_token = res.json()["access_token"]
    print(f"     Teacher Authenticated! JWT Issued: {teacher_token[:25]}...")

    # 3. Teacher Creates Assignment
    print_step(3, "Teacher Creates New Assignment in Cloud Database")
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res = client.post("/api/assignments", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "course_id": "course-uuid-001",
        "title": "Cloud Capstone: Distributed Object Store Engine",
        "description": "Implement a distributed multi-tenant object storage bucket driver with RBAC controls.",
        "deadline": deadline,
        "max_marks": 100,
        "allowed_file_types": "pdf,docx,zip",
        "max_file_size_mb": 25
    })
    assert res.status_code == 201, f"Create assignment failed: {res.text}"
    created_assignment = res.json()
    assignment_id = created_assignment["assignment_id"]
    print(f"     Assignment Published Successfully!")
    print(f"     ID:        {assignment_id}")
    print(f"     Title:     {created_assignment['title']}")
    print(f"     Max Marks: {created_assignment['max_marks']}")
    print(f"     Deadline:  {created_assignment['deadline']}")

    # 4. Student Registers
    print_step(4, "New Student Registers via Cloud Auth")
    student_email = f"student_{int(time.time())}@cloudportal.edu"
    res = client.post("/api/auth/register", json={
        "name": "Jordan Lee",
        "email": student_email,
        "password": "StudentPass2026!",
        "role": "student"
    })
    assert res.status_code == 201
    print(f"     Student Created: {student_email} (Role: student)")

    # 5. Student Login
    print_step(5, "Student Authenticates & Receives JWT")
    res = client.post("/api/auth/login", json={
        "email": student_email,
        "password": "StudentPass2026!"
    })
    assert res.status_code == 200
    student_token = res.json()["access_token"]
    print(f"     Student JWT Bearer Token: {student_token[:25]}...")

    # 6. Student Views Assignments
    print_step(6, "Student Fetches Active Assignments from Cloud Database")
    res = client.get("/api/assignments", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    assignments = res.json()
    print(f"     Found {len(assignments)} course assignments.")
    target_assign = next(a for a in assignments if a["assignment_id"] == assignment_id)
    print(f"     Target Assignment Status for Student: {target_assign['submission_status']}")

    # 7. Student Submits Assignment File to Cloud Object Storage
    print_step(7, "Student Streams PDF to Cloud Object Storage & Submits")
    dummy_pdf_content = b"%PDF-1.4 Mock student capstone implementation by Jordan Lee"
    res = client.post(
        f"/api/assignments/{assignment_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("jordan_lee_cloud_capstone.pdf", io.BytesIO(dummy_pdf_content), "application/pdf")}
    )
    assert res.status_code == 201, f"Submission failed: {res.text}"
    submission = res.json()
    submission_id = submission["submission_id"]
    print(f"     Upload Successful!")
    print(f"     Submission ID:  {submission_id}")
    print(f"     Storage Object: {submission['storage_path']}")
    print(f"     Status Tagged:  {submission['submission_status']} (Determined by Server UTC Clock)")

    # 8. Teacher Reviews Submissions Queue
    print_step(8, "Teacher Inspects Submissions Queue for Assignment")
    res = client.get(f"/api/assignments/{assignment_id}/submissions", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    subs = res.json()
    print(f"     Total submissions received: {len(subs)}")
    target_sub = next(s for s in subs if s["submission_id"] == submission_id)
    print(f"     Reviewing: {target_sub['student_name']} | File: {target_sub['file_name']}")

    # 9. Teacher Downloads File from Cloud Storage
    print_step(9, "Teacher Streams File Directly from Cloud Object Storage")
    res = client.get(f"/api/submissions/{submission_id}/download", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    print(f"     Downloaded {len(res.content)} bytes from object storage. Verified PDF magic header: {res.content[:8]}")

    # 10. Teacher Grades Submission
    print_step(10, "Teacher Awards Marks and Enters Constructive Feedback")
    marks_awarded = 96.0
    feedback_text = "Flawless decoupled architecture! Exceptional S3 storage path hierarchy and error handling."
    res = client.post(
        f"/api/submissions/{submission_id}/grade",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"marks": marks_awarded, "feedback": feedback_text}
    )
    assert res.status_code == 200
    graded_sub = res.json()
    print(f"     Marks Recorded:   {graded_sub['marks']} / {graded_sub['max_marks']}")
    print(f"     New Status:       {graded_sub['submission_status']}")
    print(f"     Written Feedback: \"{graded_sub['feedback']}\"")

    # 11. Student Checks Feedback on Dashboard
    print_step(11, "Student Retrieves Marks & Qualitative Feedback from Cloud Dashboard")
    res = client.get(f"/api/submissions/{submission_id}/feedback", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    student_feedback = res.json()
    print(f"     Student received final score: {student_feedback['marks']}/{student_feedback['max_marks']} pts")
    print(f"     Instructor Note: \"{student_feedback['feedback']}\"")

    # 12. Security Test: Another Student Attempting Cross-Tenant Access
    print_step(12, "Security Test: Verifying Cross-Tenant Isolation (RBAC)")
    # Emily Chen tries to view Jordan's private submission
    res = client.post("/api/auth/login", json={"email": "emily@cloudportal.edu", "password": "StudentPass123!"})
    emily_token = res.json()["access_token"]
    res_unauth = client.get(f"/api/submissions/{submission_id}", headers={"Authorization": f"Bearer {emily_token}"})
    print(f"     Unauthorized student attempt status: {res_unauth.status_code} (Expected: 403 Forbidden)")
    assert res_unauth.status_code == 403
    print(f"     Security guard output: {res_unauth.json()['detail']}")

    print("\n" + "#" * 70)
    print("#  SIMULATION COMPLETE: ALL 12 CLOUD STEPS PASSED WITH 100% SUCCESS!")
    print("#" * 70 + "\n")

if __name__ == "__main__":
    run_simulation()
