import uvicorn
from backend.config import HOST, PORT

if __name__ == "__main__":
    print("=" * 70)
    print("  Cloud-Based Student Assignment Submission & Feedback Portal")
    print("=" * 70)
    print(f"  Server URL:    http://{HOST}:{PORT}")
    print(f"  API Docs:      http://{HOST}:{PORT}/docs")
    print(f"  Pre-seeded Logins:")
    print(f"    - Teacher: teacher@cloudportal.edu | TeacherPass123!")
    print(f"    - Student: student@cloudportal.edu | StudentPass123!")
    print("=" * 70)
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
