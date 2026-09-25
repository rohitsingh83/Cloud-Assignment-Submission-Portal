import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserRole:
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class SubmissionStatus:
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"
    GRADED = "GRADED"

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")
    submissions = relationship("Submission", foreign_keys="Submission.student_id", back_populates="student")

class Course(Base):
    __tablename__ = "courses"

    course_id = Column(String(36), primary_key=True, default=generate_uuid)
    course_name = Column(String(150), nullable=False)
    course_code = Column(String(50), nullable=False, unique=True, index=True)
    teacher_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    teacher = relationship("User", back_populates="courses")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")

class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(36), ForeignKey("courses.course_id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=False, index=True)
    max_marks = Column(Integer, nullable=False, default=100)
    allowed_file_types = Column(String(100), default="pdf,docx,zip,png,jpg")
    max_file_size_mb = Column(Integer, default=25)
    created_by = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course", back_populates="assignments")
    creator = relationship("User")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.assignment_id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    submission_status = Column(String(20), default=SubmissionStatus.SUBMITTED, nullable=False)
    marks = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(String(36), ForeignKey("users.user_id"), nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id], back_populates="submissions")
    grader = relationship("User", foreign_keys=[graded_by])
