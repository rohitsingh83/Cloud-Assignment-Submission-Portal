from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.database import get_db_cursor
from backend.schemas import (
    StudentDashboardStats,
    TeacherDashboardStats,
    AssignmentResponse,
    SubmissionResponse
)
from backend.auth import require_student, require_teacher

router = APIRouter(prefix="/api/dashboard", tags=["Dashboards"])

@router.get("/student", response_model=StudentDashboardStats)
def get_student_dashboard(current_student: dict = Depends(require_student)):
    """Computes real-time statistics and upcoming deadlines for student dashboard."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM assignments")
        total_assignments = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT s.*, a.title AS assignment_title, a.max_marks, c.course_code
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN courses c ON a.course_id = c.course_id
            WHERE s.student_id = ?
        """, (current_student["user_id"],))
        student_subs = cursor.fetchall()

        submitted_count = len(student_subs)
        pending_count = max(0, total_assignments - submitted_count)
        late_count = sum(1 for s in student_subs if s["submission_status"] == "LATE")
        graded_count = sum(1 for s in student_subs if s["submission_status"] == "GRADED")

        # Upcoming assignments
        cursor.execute("""
            SELECT a.*, c.course_name, c.course_code
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            ORDER BY a.deadline ASC
            LIMIT 5
        """)
        upcoming_rows = cursor.fetchall()
        sub_dict = {s["assignment_id"]: dict(s) for s in student_subs}

        upcoming_list = []
        for row in upcoming_rows:
            item = dict(row)
            if item["assignment_id"] in sub_dict:
                s = sub_dict[item["assignment_id"]]
                item["has_submitted"] = True
                item["submission_status"] = s["submission_status"]
                item["student_marks"] = s["marks"]
                item["submission_id"] = s["submission_id"]
            else:
                item["has_submitted"] = False
                item["submission_status"] = "NOT_SUBMITTED"
            upcoming_list.append(item)

        # Recent feedback
        cursor.execute("""
            SELECT s.*, a.title AS assignment_title, a.max_marks, c.course_code
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN courses c ON a.course_id = c.course_id
            WHERE s.student_id = ? AND s.submission_status = 'GRADED'
            ORDER BY s.graded_at DESC
            LIMIT 5
        """, (current_student["user_id"],))
        feedback_rows = cursor.fetchall()
        feedback_list = [dict(r) for r in feedback_rows]

    return {
        "total_assignments": total_assignments,
        "pending_assignments": pending_count,
        "submitted_assignments": submitted_count,
        "late_assignments": late_count,
        "graded_assignments": graded_count,
        "upcoming_deadlines": upcoming_list,
        "recent_feedback": feedback_list
    }

@router.get("/teacher", response_model=TeacherDashboardStats)
def get_teacher_dashboard(current_teacher: dict = Depends(require_teacher)):
    """Computes real-time statistics and review queues for teacher dashboard."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM assignments")
        total_assignments = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM courses")
        total_courses = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM submissions")
        total_submissions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM submissions WHERE submission_status IN ('SUBMITTED', 'LATE')")
        pending_reviews = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM submissions WHERE submission_status = 'LATE'")
        late_submissions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM submissions WHERE submission_status = 'GRADED'")
        graded_submissions = cursor.fetchone()["total"]

        # Recent 10 submissions
        cursor.execute("""
            SELECT s.*, a.title AS assignment_title, a.max_marks, c.course_code,
                   u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN courses c ON a.course_id = c.course_id
            JOIN users u ON s.student_id = u.user_id
            ORDER BY s.submitted_at DESC
            LIMIT 10
        """)
        recent_rows = cursor.fetchall()
        recent_submissions = [dict(r) for r in recent_rows]

        # Upcoming deadlines
        cursor.execute("""
            SELECT a.*, c.course_name, c.course_code
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            ORDER BY a.deadline ASC
            LIMIT 5
        """)
        upcoming_rows = cursor.fetchall()
        upcoming_deadlines = [dict(r) for r in upcoming_rows]

    return {
        "total_assignments": total_assignments,
        "total_courses": total_courses,
        "total_submissions": total_submissions,
        "pending_reviews": pending_reviews,
        "late_submissions": late_submissions,
        "graded_submissions": graded_submissions,
        "recent_submissions": recent_submissions,
        "upcoming_deadlines": upcoming_deadlines
    }
