import os
import sys
import uvicorn

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app
from backend.config import HOST, PORT

if __name__ == "__main__":
    port = int(os.getenv("PORT", PORT))
    host = os.getenv("HOST", HOST)
    print("=" * 70)
    print("  Cloud-Based Student Assignment Submission & Feedback Portal")
    print("=" * 70)
    print(f"  Server URL:          http://{host}:{port}")
    print(f"  Interactive Docs:    http://{host}:{port}/docs")
    print(f"  Pre-seeded Logins:")
    print(f"    - Teacher: teacher@cloudportal.edu | TeacherPass123!")
    print(f"    - Student: student@cloudportal.edu | StudentPass123!")
    print("=" * 70)
    uvicorn.run("main:app", host=host, port=port, reload=True)
