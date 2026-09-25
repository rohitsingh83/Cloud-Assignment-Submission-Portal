import os
import re
import shutil
import time
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from backend.config import (
    STORAGE_DRIVER,
    STORAGE_BUCKET_NAME,
    LOCAL_STORAGE_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS
)
from backend.cloud.supabase_service import supabase_service

class CloudObjectStorageService:
    """
    Cloud Object Storage Service abstraction layer.
    
    Supports:
    - 'supabase': Native Supabase S3-compatible cloud object storage bucket.
    - 'local': Local simulated cloud storage hierarchy (assignments/{aid}/{sid}/{file}).
    """

    def __init__(self):
        self.driver = STORAGE_DRIVER
        self.bucket_name = STORAGE_BUCKET_NAME
        self.base_dir = Path(LOCAL_STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes filename to prevent directory traversal and invalid characters."""
        clean = Path(filename).name
        clean = re.sub(r"[^\w\.-]", "_", clean)
        return clean or "submission_file"

    def validate_file(self, file: UploadFile, content: bytes) -> None:
        """Validates extension and file size against cloud security policies."""
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{ext}' is not permitted. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({size_mb:.2f} MB) exceeds maximum limit of {MAX_FILE_SIZE_MB} MB"
            )

    async def upload_file(
        self,
        file: UploadFile,
        assignment_id: str,
        student_id: str
    ) -> Tuple[str, str, int]:
        """
        Uploads an object into cloud storage.
        
        Returns:
            storage_path (key in bucket)
            file_url (accessible download URI)
            file_size_bytes
        """
        content = await file.read()
        self.validate_file(file, content)

        clean_filename = self.sanitize_filename(file.filename)
        timestamp = int(time.time())
        stored_filename = f"{timestamp}_{clean_filename}"

        # Cloud Object Key: assignments/<assignment_id>/<student_id>/<filename>
        storage_path = f"assignments/{assignment_id}/{student_id}/{stored_filename}"

        # 1. Write to local storage cache
        target_file_path = self.base_dir / storage_path
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_file_path, "wb") as f:
            f.write(content)

        file_size_bytes = len(content)
        file_url = f"/api/submissions/download-by-path?path={storage_path}"

        # 2. If Supabase Cloud Storage is configured, sync object into Supabase Bucket
        if supabase_service.is_configured() and self.driver == "supabase":
            try:
                ct = file.content_type or "application/octet-stream"
                _, supabase_url, _ = supabase_service.upload_file(
                    object_path=storage_path,
                    content=content,
                    content_type=ct
                )
                file_url = supabase_url
            except Exception as e:
                # Log and fallback to local endpoint if Supabase bucket isn't provisioned yet
                print(f"[STORAGE WARNING] Supabase upload failed, using local vault: {e}")

        return storage_path, file_url, file_size_bytes

    def get_file_path(self, storage_path: str) -> Path:
        """Resolves object key to local filesystem path with path-traversal protection."""
        resolved = (self.base_dir / storage_path).resolve()
        
        # Security: Prevent path traversal outside storage bucket
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Invalid storage path reference"
            )

        # If not present on local disk, pull from Supabase Cloud Storage if available
        if not resolved.exists() and supabase_service.is_configured():
            try:
                content = supabase_service.download_file(storage_path)
                resolved.parent.mkdir(parents=True, exist_ok=True)
                with open(resolved, "wb") as f:
                    f.write(content)
                return resolved
            except Exception:
                pass

        if not resolved.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in object storage"
            )
        return resolved

    def delete_file(self, storage_path: str) -> bool:
        """Deletes object from storage."""
        # Delete from Supabase if configured
        if supabase_service.is_configured() and self.driver == "supabase":
            supabase_service.delete_file(storage_path)

        try:
            target = self.get_file_path(storage_path)
            if target.is_file():
                target.unlink()
                return True
        except HTTPException:
            pass
        return False

# Global Singleton
storage_service = CloudObjectStorageService()
