import uuid
from datetime import datetime, timedelta, timezone
from backend.database import get_db_cursor
from backend.auth import get_password_hash

def seed_initial_demo_data():
    """
    Seeds initial demo data if database is empty:
    - 1 Teacher: Prof. Sarah Johnson (teacher@cloudportal.edu / TeacherPass123!)
    - 2 Students: Alex Rivera (student@cloudportal.edu / StudentPass123!) & Emily Chen
    - 1 Course: CS-401 Cloud Computing & Distributed Systems
    - 2 Assignments: Active Cloud Storage Assignment and Past Docker Lab Assignment
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    future_deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    past_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    with get_db_cursor() as cursor:
        # Check Teacher
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ("teacher@cloudportal.edu",))
        teacher = cursor.fetchone()
        if not teacher:
            teacher_id = "teacher-uuid-001"
            cursor.execute("""
                INSERT INTO users (user_id, name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                teacher_id,
                "Prof. Sarah Johnson",
                "teacher@cloudportal.edu",
                get_password_hash("TeacherPass123!"),
                "teacher",
                now_iso
            ))
        else:
            teacher_id = teacher["user_id"]

        # Check Student 1
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ("student@cloudportal.edu",))
        student1 = cursor.fetchone()
        if not student1:
            cursor.execute("""
                INSERT INTO users (user_id, name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "student-uuid-001",
                "Alex Rivera",
                "student@cloudportal.edu",
                get_password_hash("StudentPass123!"),
                "student",
                now_iso
            ))

        # Check Student 2
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ("emily@cloudportal.edu",))
        student2 = cursor.fetchone()
        if not student2:
            cursor.execute("""
                INSERT INTO users (user_id, name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "student-uuid-002",
                "Emily Chen",
                "emily@cloudportal.edu",
                get_password_hash("StudentPass123!"),
                "student",
                now_iso
            ))

        # Check Course
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ("CS-401",))
        course = cursor.fetchone()
        if not course:
            course_id = "course-uuid-001"
            cursor.execute("""
                INSERT INTO courses (course_id, course_name, course_code, teacher_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                course_id,
                "Cloud Computing & Distributed Systems",
                "CS-401",
                teacher_id,
                now_iso
            ))
        else:
            course_id = course["course_id"]

        # Check Assignment 1
        cursor.execute("SELECT assignment_id FROM assignments WHERE assignment_id = ?", ("assign-uuid-001",))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO assignments (assignment_id, course_id, title, description, deadline, max_marks, allowed_file_types, max_file_size_mb, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "assign-uuid-001",
                course_id,
                "Assignment 1: Cloud Storage Architecture",
                "Design an object storage and metadata pipeline comparing block, file, and object storage in AWS/GCP.",
                future_deadline,
                100,
                "pdf,docx,zip",
                25,
                teacher_id,
                now_iso
            ))

        # Check Assignment 2 (Past deadline for late testing)
        cursor.execute("SELECT assignment_id FROM assignments WHERE assignment_id = ?", ("assign-uuid-002",))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO assignments (assignment_id, course_id, title, description, deadline, max_marks, allowed_file_types, max_file_size_mb, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "assign-uuid-002",
                course_id,
                "Assignment 2: Docker Containerization Lab",
                "Containerize a microservice backend and verify orchestration and resource constraints.",
                past_deadline,
                50,
                "pdf,zip",
                20,
                teacher_id,
                now_iso
            ))
