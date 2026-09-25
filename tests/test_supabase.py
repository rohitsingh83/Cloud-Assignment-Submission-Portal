import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.cloud.supabase_service import SupabaseCloudService, supabase_service
from backend.database import PostgresCursorWrapper, IS_POSTGRES

@pytest.fixture
def client():
    return TestClient(app)

def test_supabase_health_in_api_probe(client):
    """Verify that /api/health includes Supabase diagnostics."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "database" in data
    assert "storage_driver" in data
    assert "supabase" in data
    assert "status" in data["supabase"]

def test_supabase_service_initialization():
    """Verify Supabase service defaults and configuration check."""
    svc = SupabaseCloudService()
    assert svc.bucket == "assignments"
    # When unconfigured, is_configured should return False
    if not (svc.url and svc.key):
        assert svc.is_configured() is False

def test_supabase_public_url_generation():
    """Verify public CDN URL generator format."""
    svc = SupabaseCloudService()
    svc.url = "https://example-project.supabase.co"
    svc.key = "fake-key"
    url = svc.get_public_url("assignments/assign-1/student-1/file.pdf")
    assert url == "https://example-project.supabase.co/storage/v1/object/public/assignments/assignments/assign-1/student-1/file.pdf"

def test_postgres_cursor_placeholder_adaptation():
    """Verify that SQLite '?' placeholders are safely adapted to PostgreSQL '%s'."""
    class DummyCursor:
        def __init__(self):
            self.last_query = None
            self.last_params = None
        def execute(self, query, params=None):
            self.last_query = query
            self.last_params = params

    dummy = DummyCursor()
    wrapper = PostgresCursorWrapper(dummy)
    
    # Single parameter
    wrapper.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
    assert wrapper.last_query == "SELECT * FROM users WHERE email = %s"
    assert wrapper.last_params == ("test@example.com",)

    # Multiple parameters
    wrapper.execute("SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?", ("a1", "s1"))
    assert wrapper.last_query == "SELECT * FROM submissions WHERE assignment_id = %s AND student_id = %s"
    assert wrapper.last_params == ("a1", "s1")
