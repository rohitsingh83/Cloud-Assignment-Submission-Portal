import mimetypes
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from backend.database import get_db_cursor
from backend.schemas import SubmissionResponse
from backend.auth import get_current_user, get_user_from_token, require_teacher, require_student
from backend.cloud.storage_service import storage_service

router = APIRouter(prefix="/api", tags=["Submissions"])

@router.post("/assignments/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: str,
    file: UploadFile = File(...),
    current_student: dict = Depends(require_student)
):
    """
    Student submits an assignment file.
    - Validates file type against assignment constraints.
    - Uploads file into Cloud Object Storage.
    - Server-side UTC deadline evaluation.
    - Saves submission record to cloud database.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM assignments WHERE assignment_id = ?", (assignment_id,))
        assignment = cursor.fetchone()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        # Validate file extension
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        allowed = [e.strip() for e in assignment["allowed_file_types"].split(",")]
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '.{ext}'. Allowed types: {assignment['allowed_file_types']}"
            )

        # Check existing submission (resubmission)
        cursor.execute("""
            SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?
        """, (assignment_id, current_student["user_id"]))
        existing_sub = cursor.fetchone()

    # Upload to Cloud Object Storage
    storage_path, file_url, file_size = await storage_service.upload_file(
        file=file,
        assignment_id=assignment_id,
        student_id=current_student["user_id"]
    )

    # Server-Side Deadline Check
    submitted_at_dt = datetime.now(timezone.utc)
    submitted_at_iso = submitted_at_dt.isoformat()

    deadline_raw = assignment["deadline"]
    if isinstance(deadline_raw, str):
        try:
            deadline_dt = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))
        except Exception:
            deadline_dt = datetime.now(timezone.utc)
    else:
        deadline_dt = deadline_raw

    if deadline_dt.tzinfo is None:
        deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)

    status_str = "SUBMITTED" if submitted_at_dt <= deadline_dt else "LATE"

    with get_db_cursor() as cursor:
        if existing_sub:
            storage_service.delete_file(existing_sub["storage_path"])
            submission_id = existing_sub["submission_id"]
            cursor.execute("""
                UPDATE submissions
                SET file_name = ?, file_url = ?, storage_path = ?, file_size_bytes = ?,
                    submitted_at = ?, submission_status = ?, marks = NULL, feedback = NULL, graded_at = NULL, graded_by = NULL
                WHERE submission_id = ?
            """, (file.filename, file_url, storage_path, file_size, submitted_at_iso, status_str, submission_id))
        else:
            submission_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO submissions (
                    submission_id, assignment_id, student_id, file_name, file_url,
                    storage_path, file_size_bytes, submitted_at, submission_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                submission_id,
                assignment_id,
                current_student["user_id"],
                file.filename,
                file_url,
                storage_path,
                file_size,
                submitted_at_iso,
                status_str
            ))

    return {
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "assignment_title": assignment["title"],
        "student_id": current_student["user_id"],
        "student_name": current_student["name"],
        "student_email": current_student["email"],
        "file_name": file.filename,
        "file_url": file_url,
        "storage_path": storage_path,
        "file_size_bytes": file_size,
        "submitted_at": submitted_at_iso,
        "submission_status": status_str,
        "max_marks": assignment["max_marks"]
    }

@router.get("/submissions/me", response_model=List[SubmissionResponse])
def get_my_submissions(current_student: dict = Depends(require_student)):
    """Student views their own historical submissions and grades."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT s.*, a.title AS assignment_title, a.max_marks, c.course_code
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN courses c ON a.course_id = c.course_id
            WHERE s.student_id = ?
            ORDER BY s.submitted_at DESC
        """, (current_student["user_id"],))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            item = dict(r)
            item["student_name"] = current_student["name"]
            item["student_email"] = current_student["email"]
            results.append(item)
        return results

@router.get("/assignments/{assignment_id}/submissions", response_model=List[SubmissionResponse])
def get_assignment_submissions(
    assignment_id: str,
    current_teacher: dict = Depends(require_teacher)
):
    """Teacher views all student submissions for an assignment."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT title, max_marks FROM assignments WHERE assignment_id = ?", (assignment_id,))
        assign = cursor.fetchone()
        if not assign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        cursor.execute("""
            SELECT s.*, u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN users u ON s.student_id = u.user_id
            WHERE s.assignment_id = ?
            ORDER BY s.submitted_at DESC
        """, (assignment_id,))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            item = dict(r)
            item["assignment_title"] = assign["title"]
            item["max_marks"] = assign["max_marks"]
            results.append(item)
        return results

@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission_details(
    submission_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Returns single submission details with RBAC ownership checks."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT s.*, a.title AS assignment_title, a.max_marks, c.course_code,
                   u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN courses c ON a.course_id = c.course_id
            JOIN users u ON s.student_id = u.user_id
            WHERE s.submission_id = ?
        """, (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        sub = dict(row)
        if current_user["role"] == "student" and sub["student_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You cannot view another student's submission"
            )
        return sub

def _resolve_user_from_request(
    authorization: Optional[str] = None,
    token: Optional[str] = None
) -> dict:
    """Helper to authenticate user via either Bearer header or query token parameter."""
    token_str = None
    if authorization and authorization.lower().startswith("bearer "):
        token_str = authorization[7:].strip()
    elif token:
        token_str = token

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
    return get_user_from_token(token_str)

@router.get("/submissions/{submission_id}/download")
def download_submission_file(
    submission_id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Authorized file download directly streaming from Cloud Object Storage."""
    current_user = _resolve_user_from_request(authorization, token)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT student_id, storage_path, file_name FROM submissions WHERE submission_id = ?", (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        if current_user["role"] == "student" and row["student_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot download assignments submitted by other students"
            )

        storage_path = row["storage_path"]
        file_name = row["file_name"]

    file_path = storage_service.get_file_path(storage_path)
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="application/octet-stream"
    )

@router.get("/submissions/{submission_id}/preview")
def preview_submission_file(
    submission_id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Inline preview endpoint for browser rendering (PDF, images, text, source code)."""
    current_user = _resolve_user_from_request(authorization, token)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT student_id, storage_path, file_name FROM submissions WHERE submission_id = ?", (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        if current_user["role"] == "student" and row["student_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot preview assignments submitted by other students"
            )

        storage_path = row["storage_path"]
        file_name = row["file_name"]

    file_path = storage_service.get_file_path(storage_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    if not mime_type:
        mime_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{file_name}"'}
    )
