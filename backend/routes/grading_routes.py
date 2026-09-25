from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import get_db_cursor
from backend.schemas import GradeSubmissionRequest, SubmissionResponse
from backend.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/submissions", tags=["Grading & Feedback"])

@router.post("/{submission_id}/grade", response_model=SubmissionResponse)
def grade_submission(
    submission_id: str,
    payload: GradeSubmissionRequest,
    current_teacher: dict = Depends(require_teacher)
):
    """Teacher grades a student submission with marks and written feedback."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT s.*, a.max_marks, a.title AS assignment_title,
                   u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN users u ON s.student_id = u.user_id
            WHERE s.submission_id = ?
        """, (submission_id,))
        sub = cursor.fetchone()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        max_marks = sub["max_marks"]
        if payload.marks > max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Awarded marks ({payload.marks}) cannot exceed maximum allowed marks ({max_marks})"
            )

        graded_at = datetime.now(timezone.utc).isoformat()
        feedback_str = payload.feedback.strip() if payload.feedback else ""

        cursor.execute("""
            UPDATE submissions
            SET marks = ?, feedback = ?, graded_at = ?, graded_by = ?, submission_status = 'GRADED'
            WHERE submission_id = ?
        """, (payload.marks, feedback_str, graded_at, current_teacher["user_id"], submission_id))

        res = dict(sub)
        res["marks"] = payload.marks
        res["feedback"] = feedback_str
        res["graded_at"] = graded_at
        res["graded_by"] = current_teacher["user_id"]
        res["submission_status"] = "GRADED"
        return res

@router.get("/{submission_id}/feedback", response_model=SubmissionResponse)
def get_submission_feedback(
    submission_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves marks and feedback for a submission."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT s.*, a.max_marks, a.title AS assignment_title,
                   u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN users u ON s.student_id = u.user_id
            WHERE s.submission_id = ?
        """, (submission_id,))
        sub = cursor.fetchone()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        item = dict(sub)
        if current_user["role"] == "student" and item["student_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You cannot access feedback belonging to another student"
            )
        return item
