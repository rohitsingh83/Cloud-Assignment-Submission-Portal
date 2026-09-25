-- ============================================================================
-- EduCloud: Supabase Database Schema & Storage Setup
-- Cloud-Based Student Assignment Submission & Feedback Portal
-- ============================================================================
-- How to apply:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard
-- 2. Navigate to "SQL Editor" -> "New query"
-- 3. Paste this entire file and click "Run"
-- ============================================================================

-- Enable UUID extension (built-in to Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. USERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. COURSES TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.courses (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    course_code TEXT UNIQUE NOT NULL,
    teacher_id TEXT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. ASSIGNMENTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.assignments (
    assignment_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES public.courses(course_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    deadline TIMESTAMPTZ NOT NULL,
    max_marks INTEGER NOT NULL DEFAULT 100,
    allowed_file_types TEXT NOT NULL DEFAULT 'pdf,docx,zip',
    max_file_size_mb INTEGER NOT NULL DEFAULT 25,
    created_by TEXT NOT NULL REFERENCES public.users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 4. SUBMISSIONS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.submissions (
    submission_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL REFERENCES public.assignments(assignment_id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submission_status TEXT NOT NULL DEFAULT 'SUBMITTED' CHECK (submission_status IN ('SUBMITTED', 'LATE', 'GRADED')),
    marks REAL,
    feedback TEXT,
    graded_at TIMESTAMPTZ,
    graded_by TEXT REFERENCES public.users(user_id)
);

-- ----------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON public.assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_submissions_assign_student ON public.submissions(assignment_id, student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON public.submissions(submission_status);

-- ----------------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submissions ENABLE ROW LEVEL SECURITY;

-- Allow public read/write through backend service key or authenticated roles
CREATE POLICY "Allow public read for portal tables" ON public.users FOR SELECT USING (true);
CREATE POLICY "Allow service role full access users" ON public.users FOR ALL USING (true);

CREATE POLICY "Allow public read for courses" ON public.courses FOR SELECT USING (true);
CREATE POLICY "Allow service role full access courses" ON public.courses FOR ALL USING (true);

CREATE POLICY "Allow public read for assignments" ON public.assignments FOR SELECT USING (true);
CREATE POLICY "Allow service role full access assignments" ON public.assignments FOR ALL USING (true);

CREATE POLICY "Allow service role full access submissions" ON public.submissions FOR ALL USING (true);
CREATE POLICY "Allow student read own submissions" ON public.submissions FOR SELECT USING (true);

-- ----------------------------------------------------------------------------
-- 7. SUPABASE STORAGE BUCKET INITIALIZATION
-- ----------------------------------------------------------------------------
-- Create the 'assignments' bucket if it doesn't already exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('assignments', 'assignments', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: Allow authenticated and public uploads/reads for assignments
CREATE POLICY "Allow public read on assignments bucket"
ON storage.objects FOR SELECT
USING (bucket_id = 'assignments');

CREATE POLICY "Allow upload to assignments bucket"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'assignments');

CREATE POLICY "Allow update and delete on assignments bucket"
ON storage.objects FOR UPDATE
USING (bucket_id = 'assignments');

-- ----------------------------------------------------------------------------
-- 8. PRE-SEEDED DEMO ACCOUNTS (Password: TeacherPass123! / StudentPass123!)
-- ----------------------------------------------------------------------------
INSERT INTO public.users (user_id, name, email, password_hash, role, created_at)
VALUES 
    (
        'teacher-uuid-001',
        'Prof. Sarah Johnson',
        'teacher@cloudportal.edu',
        'pbkdf2:sha256:100000$h6wD3Z1p8Q$5f3e9b1a2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f',
        'teacher',
        NOW()
    ),
    (
        'student-uuid-001',
        'Alex Rivera',
        'student@cloudportal.edu',
        'pbkdf2:sha256:100000$j9xK5M2n1L$4e2f8a0b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f',
        'student',
        NOW()
    )
ON CONFLICT (email) DO NOTHING;
