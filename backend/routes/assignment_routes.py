import io
import csv
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response

from backend.database import get_db_cursor
from backend.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    CourseResponse,
    MessageResponse
)
from backend.auth import get_current_user, require_teacher

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])

@router.get("/courses", response_model=List[CourseResponse])
def list_courses(current_user: dict = Depends(get_current_user)):
    """Retrieves all registered courses."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT course_id, course_name, course_code, teacher_id, created_at FROM courses")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_teacher: dict = Depends(require_teacher)
):
    """Teacher creates a new assignment with strict deadline and validation rules."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT course_id, course_name, course_code FROM courses WHERE course_id = ?", (payload.course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        assignment_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        deadline_str = payload.deadline.isoformat()

        cursor.execute("""
            INSERT INTO assignments (
                assignment_id, course_id, title, description, deadline,
                max_marks, allowed_file_types, max_file_size_mb, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment_id,
            payload.course_id,
            payload.title.strip(),
            payload.description.strip() if payload.description else "",
            deadline_str,
            payload.max_marks,
            payload.allowed_file_types.lower().replace(" ", ""),
            payload.max_file_size_mb,
            current_teacher["user_id"],
            created_at
        ))

    return {
        "assignment_id": assignment_id,
        "course_id": payload.course_id,
        "course_name": course["course_name"],
        "course_code": course["course_code"],
        "title": payload.title.strip(),
        "description": payload.description.strip() if payload.description else "",
        "deadline": payload.deadline,
        "max_marks": payload.max_marks,
        "allowed_file_types": payload.allowed_file_types.lower().replace(" ", ""),
        "max_file_size_mb": payload.max_file_size_mb,
        "created_by": current_teacher["user_id"],
        "created_at": created_at,
        "submission_status": "NOT_SUBMITTED",
        "has_submitted": False
    }

@router.get("", response_model=List[AssignmentResponse])
def get_assignments(
    course_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves list of assignments with computed student submission state."""
    with get_db_cursor() as cursor:
        query = """
            SELECT a.assignment_id, a.course_id, c.course_name, c.course_code,
                   a.title, a.description, a.deadline, a.max_marks,
                   a.allowed_file_types, a.max_file_size_mb, a.created_by, a.created_at
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
        """
        params = []
        if course_id:
            query += " WHERE a.course_id = ?"
            params.append(course_id)
        query += " ORDER BY a.deadline ASC"

        cursor.execute(query, params)
        assignments = cursor.fetchall()

        results = []
        for a in assignments:
            item = dict(a)
            if current_user["role"] == "student":
                cursor.execute("""
                    SELECT submission_id, submission_status, marks
                    FROM submissions
                    WHERE assignment_id = ? AND student_id = ?
                """, (item["assignment_id"], current_user["user_id"]))
                sub = cursor.fetchone()
                if sub:
                    item["has_submitted"] = True
                    item["submission_status"] = sub["submission_status"]
                    item["student_marks"] = sub["marks"]
                    item["submission_id"] = sub["submission_id"]
                else:
                    item["has_submitted"] = False
                    item["submission_status"] = "NOT_SUBMITTED"
            results.append(item)

        return results

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment_by_id(
    assignment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves single assignment details."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT a.assignment_id, a.course_id, c.course_name, c.course_code,
                   a.title, a.description, a.deadline, a.max_marks,
                   a.allowed_file_types, a.max_file_size_mb, a.created_by, a.created_at
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            WHERE a.assignment_id = ?
        """, (assignment_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        item = dict(row)
        if current_user["role"] == "student":
            cursor.execute("""
                SELECT submission_id, submission_status, marks
                FROM submissions
                WHERE assignment_id = ? AND student_id = ?
            """, (assignment_id, current_user["user_id"]))
            sub = cursor.fetchone()
            if sub:
                item["has_submitted"] = True
                item["submission_status"] = sub["submission_status"]
                item["student_marks"] = sub["marks"]
                item["submission_id"] = sub["submission_id"]
            else:
                item["has_submitted"] = False
                item["submission_status"] = "NOT_SUBMITTED"

        return item

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    current_teacher: dict = Depends(require_teacher)
):
    """Teacher updates assignment details."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM assignments WHERE assignment_id = ?", (assignment_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        title = payload.title.strip() if payload.title is not None else existing["title"]
        desc = payload.description.strip() if payload.description is not None else existing["description"]
        deadline = payload.deadline.isoformat() if payload.deadline is not None else existing["deadline"]
        max_marks = payload.max_marks if payload.max_marks is not None else existing["max_marks"]
        types = payload.allowed_file_types.lower().replace(" ", "") if payload.allowed_file_types is not None else existing["allowed_file_types"]
        max_mb = payload.max_file_size_mb if payload.max_file_size_mb is not None else existing["max_file_size_mb"]

        cursor.execute("""
            UPDATE assignments
            SET title = ?, description = ?, deadline = ?, max_marks = ?, allowed_file_types = ?, max_file_size_mb = ?
            WHERE assignment_id = ?
        """, (title, desc, deadline, max_marks, types, max_mb, assignment_id))

        cursor.execute("""
            SELECT a.*, c.course_name, c.course_code
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            WHERE a.assignment_id = ?
        """, (assignment_id,))
        return dict(cursor.fetchone())

@router.delete("/{assignment_id}", response_model=MessageResponse)
def delete_assignment(
    assignment_id: str,
    current_teacher: dict = Depends(require_teacher)
):
    """Teacher deletes an assignment and related submissions."""
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM assignments WHERE assignment_id = ?", (assignment_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return MessageResponse(message="Assignment deleted successfully")

@router.get("/{assignment_id}/export-csv")
def export_assignment_grades_csv(
    assignment_id: str,
    current_teacher: dict = Depends(require_teacher)
):
    """Generates and downloads an official CSV gradebook for an assignment."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT title, max_marks FROM assignments WHERE assignment_id = ?", (assignment_id,))
        assign = cursor.fetchone()
        if not assign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        cursor.execute("""
            SELECT u.name AS student_name, u.email AS student_email,
                   s.file_name, s.submitted_at, s.submission_status, s.marks, s.feedback
            FROM submissions s
            JOIN users u ON s.student_id = u.user_id
            WHERE s.assignment_id = ?
            ORDER BY u.name ASC
        """, (assignment_id,))
        rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Email", "Submission File", "Submitted At (UTC)", "Status", f"Marks (Out of {assign['max_marks']})", "Feedback"])

    for r in rows:
        writer.writerow([
            r["student_name"],
            r["student_email"],
            r["file_name"],
            r["submitted_at"],
            r["submission_status"],
            r["marks"] if r["marks"] is not None else "Ungraded",
            r["feedback"] or "No comments"
        ])

    csv_data = output.getvalue()
    clean_title = "".join(c if c.isalnum() else "_" for c in assign["title"])[:30]
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=grades_{clean_title}.csv"}
    )
