import os
import mimetypes
from typing import Optional, Tuple
import httpx
from backend.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_STORAGE_BUCKET,
    MAX_FILE_SIZE_MB
)

class SupabaseCloudService:
    """
    Supabase Cloud Integration Service.
    
    Provides native access to Supabase:
    1. Cloud Object Storage (S3-compatible bucket) for assignment submissions (PDFs, ZIPs, DOCX).
    2. Connection diagnostics and health monitoring.
    3. Public CDN URL generation for uploaded student submissions.
    """

    def __init__(self):
        self.url = (SUPABASE_URL or "").rstrip("/")
        self.key = SUPABASE_KEY or ""
        self.bucket = SUPABASE_STORAGE_BUCKET or "assignments"

    def is_configured(self) -> bool:
        """Returns True if Supabase project URL and API key are configured."""
        return bool(self.url and self.key)

    def _headers(self, content_type: Optional[str] = None) -> dict:
        """Constructs authenticated Supabase headers."""
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def get_public_url(self, object_path: str, bucket: Optional[str] = None) -> str:
        """Generates the direct public CDN URL for an object in a Supabase bucket."""
        target_bucket = bucket or self.bucket
        clean_path = object_path.lstrip("/")
        return f"{self.url}/storage/v1/object/public/{target_bucket}/{clean_path}"

    def upload_file(
        self,
        object_path: str,
        content: bytes,
        content_type: Optional[str] = None,
        bucket: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Uploads binary bytes to a Supabase Cloud Storage bucket.
        
        Returns:
            storage_path (key in bucket)
            file_url (accessible Supabase CDN URL)
            file_size_bytes
        """
        if not self.is_configured():
            raise RuntimeError("Supabase credentials not configured in environment (SUPABASE_URL / SUPABASE_KEY).")

        target_bucket = bucket or self.bucket
        clean_path = object_path.lstrip("/")
        endpoint = f"{self.url}/storage/v1/object/{target_bucket}/{clean_path}"

        ct = content_type or mimetypes.guess_type(clean_path)[0] or "application/octet-stream"
        headers = self._headers(content_type=ct)
        headers["x-upsert"] = "true"

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, content=content, headers=headers)
            if resp.status_code not in (200, 201):
                # If bucket doesn't exist, provide clear error message
                err_detail = resp.text
                raise RuntimeError(
                    f"Supabase Storage upload failed ({resp.status_code}): {err_detail}. "
                    f"Ensure bucket '{target_bucket}' exists in your Supabase project."
                )

        file_url = self.get_public_url(clean_path, target_bucket)
        return clean_path, file_url, len(content)

    def download_file(self, object_path: str, bucket: Optional[str] = None) -> bytes:
        """Downloads/streams file bytes directly from Supabase Cloud Storage."""
        if not self.is_configured():
            raise RuntimeError("Supabase credentials not configured.")

        target_bucket = bucket or self.bucket
        clean_path = object_path.lstrip("/")

        # First attempt authenticated storage endpoint
        endpoint = f"{self.url}/storage/v1/object/authenticated/{target_bucket}/{clean_path}"
        headers = self._headers()

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(endpoint, headers=headers)
            if resp.status_code == 200:
                return resp.content
            # Fallback to public storage endpoint
            pub_endpoint = f"{self.url}/storage/v1/object/public/{target_bucket}/{clean_path}"
            pub_resp = client.get(pub_endpoint, headers=headers)
            if pub_resp.status_code == 200:
                return pub_resp.content

            raise FileNotFoundError(
                f"File '{clean_path}' not found in Supabase bucket '{target_bucket}' (HTTP {resp.status_code})"
            )

    def delete_file(self, object_path: str, bucket: Optional[str] = None) -> bool:
        """Deletes an object from Supabase Cloud Storage."""
        if not self.is_configured():
            return False

        target_bucket = bucket or self.bucket
        clean_path = object_path.lstrip("/")
        endpoint = f"{self.url}/storage/v1/object/{target_bucket}"
        headers = self._headers(content_type="application/json")

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.request("DELETE", endpoint, json={"prefixes": [clean_path]}, headers=headers)
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def health_check(self) -> dict:
        """Performs a lightweight liveness probe against the Supabase project."""
        if not self.is_configured():
            return {
                "enabled": False,
                "status": "unconfigured",
                "message": "Set SUPABASE_URL and SUPABASE_KEY to activate cloud storage & database."
            }

        try:
            endpoint = f"{self.url}/storage/v1/bucket"
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(endpoint, headers=self._headers())
                if resp.status_code == 200:
                    buckets = [b.get("name") for b in resp.json() if isinstance(b, dict)]
                    has_target = self.bucket in buckets
                    return {
                        "enabled": True,
                        "status": "connected",
                        "project_url": self.url,
                        "active_bucket": self.bucket,
                        "bucket_exists": has_target,
                        "all_buckets": buckets
                    }
                return {
                    "enabled": True,
                    "status": "error",
                    "http_code": resp.status_code,
                    "detail": resp.text
                }
        except Exception as e:
            return {
                "enabled": True,
                "status": "unreachable",
                "error": str(e)
            }

# Global Singleton
supabase_service = SupabaseCloudService()
