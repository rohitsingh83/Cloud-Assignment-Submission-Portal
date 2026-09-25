from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ----------------- User Schemas -----------------
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="student", pattern="^(student|teacher|admin)$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: str
    email: str
    role: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ----------------- Course Schemas -----------------
class CourseCreate(BaseModel):
    course_name: str = Field(..., min_length=3, max_length=150)
    course_code: str = Field(..., min_length=2, max_length=20)

class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    course_name: str
    course_code: str
    teacher_id: str
    created_at: datetime

# ----------------- Assignment Schemas -----------------
class AssignmentCreate(BaseModel):
    course_id: str
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    deadline: datetime
    max_marks: int = Field(default=100, ge=1, le=1000)
    allowed_file_types: str = Field(default="pdf,docx,zip,png,jpg")
    max_file_size_mb: int = Field(default=25, ge=1, le=100)

class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_marks: Optional[int] = Field(None, ge=1, le=1000)
    allowed_file_types: Optional[str] = None
    max_file_size_mb: Optional[int] = Field(None, ge=1, le=100)

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: str
    course_id: str
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    deadline: datetime
    max_marks: int
    allowed_file_types: str
    max_file_size_mb: int
    created_by: str
    created_at: datetime
    # Computed fields for student view
    submission_status: Optional[str] = None
    student_marks: Optional[float] = None
    has_submitted: Optional[bool] = False
    submission_id: Optional[str] = None

# ----------------- Submission & Grading Schemas -----------------
class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    assignment_id: str
    assignment_title: Optional[str] = None
    course_code: Optional[str] = None
    student_id: str
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    file_name: str
    file_url: str
    storage_path: str
    file_size_bytes: int
    submitted_at: datetime
    submission_status: str
    marks: Optional[float] = None
    feedback: Optional[str] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None
    max_marks: Optional[int] = 100

class GradeSubmissionRequest(BaseModel):
    marks: float = Field(..., ge=0)
    feedback: Optional[str] = Field(default="", max_length=2000)

# ----------------- Dashboard Schemas -----------------
class StudentDashboardStats(BaseModel):
    total_assignments: int
    pending_assignments: int
    submitted_assignments: int
    late_assignments: int
    graded_assignments: int
    upcoming_deadlines: List[AssignmentResponse]
    recent_feedback: List[SubmissionResponse]

class TeacherDashboardStats(BaseModel):
    total_assignments: int
    total_courses: int
    total_submissions: int
    pending_reviews: int
    late_submissions: int
    graded_submissions: int
    recent_submissions: List[SubmissionResponse]
    upcoming_deadlines: List[AssignmentResponse]

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
